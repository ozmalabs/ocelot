use rustc_hash::FxHashMap;
use serde_json::json;
use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::{Arc, Barrier, Mutex};
use std::thread;
use std::time::Instant;
use substrate_rs::checker::ConsistencyChecker;
use substrate_rs::grammar::Grammar;
use substrate_rs::graph::{Attrs, NodeID};
use substrate_rs::substrate::{ExperimentSnapshot, Substrate};
use substrate_rs::value::{SurfaceKind, Value};

struct Meter;
static LIVE: AtomicUsize = AtomicUsize::new(0);
unsafe impl GlobalAlloc for Meter {
    unsafe fn alloc(&self, l: Layout) -> *mut u8 { let p=System.alloc(l); if !p.is_null(){LIVE.fetch_add(l.size(),Ordering::SeqCst);} p }
    unsafe fn alloc_zeroed(&self, l: Layout) -> *mut u8 { let p=System.alloc_zeroed(l); if !p.is_null(){LIVE.fetch_add(l.size(),Ordering::SeqCst);} p }
    unsafe fn dealloc(&self,p:*mut u8,l:Layout){LIVE.fetch_sub(l.size(),Ordering::SeqCst);System.dealloc(p,l)}
    unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{let q=System.realloc(p,l,n);if !q.is_null(){if n>=l.size(){LIVE.fetch_add(n-l.size(),Ordering::SeqCst);}else{LIVE.fetch_sub(l.size()-n,Ordering::SeqCst);}}q}
}
#[global_allocator]
static ALLOCATOR: Meter = Meter;

#[derive(Clone,Copy)] enum Topology { Path, RegularFour, Star, Grid }
impl Topology { fn name(self)->&'static str { match self {Self::Path=>"path",Self::RegularFour=>"regular_four",Self::Star=>"star",Self::Grid=>"grid"} } }
#[derive(Clone,Copy)] enum TargetPolicy { Clustered, Spread, LowDegree, HighDegree }
impl TargetPolicy { fn name(self)->&'static str { match self {Self::Clustered=>"clustered",Self::Spread=>"spread",Self::LowDegree=>"low_out_degree",Self::HighDegree=>"high_out_degree"} } }
#[derive(Clone,Copy)] enum Backend { Shared, Eager }
impl Backend { fn name(self)->&'static str { match self {Self::Shared=>"shared_snapshot",Self::Eager=>"eager_copy"} } }

struct Fixture { primary:Arc<Substrate>, base_type:substrate_rs::sym::Sym, marker:substrate_rs::sym::Sym,
    base_edge:substrate_rs::sym::Sym, branch_edge:substrate_rs::sym::Sym, base_edges:usize }

fn thread_only_delta(fanout:usize)->i64 {
    let ready=Arc::new(Barrier::new(fanout+1));let cancel=Arc::new(Barrier::new(fanout+1));
    let after=Arc::new(Barrier::new(fanout+1));let release=Arc::new(Barrier::new(fanout+1));
    let before=LIVE.load(Ordering::SeqCst);let mut ws=Vec::with_capacity(fanout);
    for _ in 0..fanout {let (r,c,a,x)=(ready.clone(),cancel.clone(),after.clone(),release.clone());
        ws.push(thread::spawn(move||{r.wait();c.wait();a.wait();x.wait();}));}
    ready.wait();cancel.wait();after.wait();release.wait();for w in ws{w.join().unwrap();}
    LIVE.load(Ordering::SeqCst) as i64-before as i64
}

fn fixture(size:usize,topology:Topology)->Fixture {
    let mut primary=Substrate::new(ConsistencyChecker::new(Grammar::new()));
    let base_type=primary.intern_symbol("MutationScaleBase");
    let marker=primary.intern_symbol("mutation_marker");
    let base_edge=primary.intern_symbol("topology_edge");
    let branch_edge=primary.intern_symbol("branch_overlay_edge");
    for i in 0..16 {primary.intern_symbol(&format!("MutationScaleBranch{i}"));}
    for _i in 0..size {let id=primary.add_node(base_type,FxHashMap::default());primary.set_attr(id,marker,Value::Int(0));}
    let mut edges=0usize;
    let mut add=|src:usize,tgt:usize|{primary.graph.insert_edge(NodeID(src as u32),base_edge,NodeID(tgt as u32),Attrs::new()).unwrap();edges+=1;};
    match topology {
        Topology::Path=>for i in 0..size.saturating_sub(1){add(i,i+1)},
        Topology::RegularFour=>for i in 0..size{for step in 1..=4{add(i,(i+step)%size)}},
        Topology::Star=>for i in 1..size{add(0,i)},
        Topology::Grid=>{let width=(size as f64).sqrt().ceil() as usize;let height=size.div_ceil(width);
            for i in 0..size{let row=i/width;let col=i%width;if col+1<width&&i+1<size{add(i,i+1)}
                let down=i+width;if row+1<height&&down<size{add(i,down)}}}
    }
    Fixture{primary:Arc::new(primary),base_type,marker,base_edge,branch_edge,base_edges:edges}
}

fn select_targets(primary:&Substrate,size:usize,count:usize,policy:TargetPolicy)->(Vec<usize>,[usize;4]){
    let degrees:Vec<usize>=(0..size).map(|i|primary.graph.out_edges_slice(NodeID(i as u32),None).len()).collect();
    let mut targets:Vec<usize>=match policy{
        TargetPolicy::Clustered=>{let start=(size-count)/2;(start..start+count).collect()},
        TargetPolicy::Spread=>(0..count).map(|j|j*size/count).collect(),
        TargetPolicy::LowDegree|TargetPolicy::HighDegree=>{
            let mut ids:Vec<usize>=(0..size).collect();
            ids.sort_by_key(|&i|if matches!(policy,TargetPolicy::LowDegree){(degrees[i],i)}else{(usize::MAX-degrees[i],i)});
            ids.truncate(count);ids
        }
    };
    targets.sort_unstable();
    let mut selected:Vec<usize>=targets.iter().map(|&i|degrees[i]).collect();selected.sort_unstable();
    let summary=[selected[0],selected[selected.len()/2],*selected.last().unwrap(),selected.iter().sum()];
    (targets,summary)
}

fn base_intact(sub:&Substrate,size:usize,base_type:substrate_rs::sym::Sym,marker:substrate_rs::sym::Sym,edges:usize)->bool{
    if sub.graph.node_count()!=size||sub.graph.edge_count()!=edges||sub.graph.nodes_of_type(base_type).len()!=size{return false;}
    (0..size).all(|i|sub.graph.node(NodeID(i as u32)).attrs.0.iter().any(|(k,v)|*k==marker&&*v==Value::Int(0)))
}

fn wave(primary:Arc<Substrate>,snapshot:Arc<ExperimentSnapshot>,f:&Fixture,size:usize,topology:Topology,
    density:usize,policy:TargetPolicy,degree_summary:[usize;4],fanout:usize,backend:Backend,repeat:usize,
    targets:Arc<Vec<usize>>,payload:Arc<[u8]>,mutate:bool)->serde_json::Value{
    let thread_control=thread_only_delta(fanout);
    let ready=Arc::new(Barrier::new(fanout+1));let cancel=Arc::new(Barrier::new(fanout+1));
    let after=Arc::new(Barrier::new(fanout+1));let release=Arc::new(Barrier::new(fanout+1));
    let cancel_count=fanout/2;let valid=Arc::new(AtomicBool::new(true));
    let ids=Arc::new(Mutex::new(Vec::with_capacity(fanout)));let mut ws=Vec::with_capacity(fanout);
    let before=LIVE.load(Ordering::SeqCst);let started=Instant::now();
    for worker in 0..fanout{
        let (p,s,r,c,a,x,v,ids2)=(primary.clone(),snapshot.clone(),ready.clone(),cancel.clone(),after.clone(),release.clone(),valid.clone(),ids.clone());
        let targets=targets.clone();let payload=payload.clone();let (base_type,marker,branch_edge,base_edges)=(f.base_type,f.marker,f.branch_edge,f.base_edges);
        ws.push(thread::spawn(move||{
            let mut branch=Some(match backend{Backend::Shared=>s.fork().unwrap(),Backend::Eager=>p.fork_full_copy_experiment().unwrap()});
            let branch_type=branch.as_ref().unwrap().interner().lookup(&format!("MutationScaleBranch{worker}")).unwrap();
            let added=if mutate{Some(branch.as_mut().unwrap().add_node(branch_type,FxHashMap::default()).0)}else{None};
            ids2.lock().unwrap().push((worker,added));
            if mutate{
                let b=branch.as_mut().unwrap();let added=added.unwrap();
                for &i in targets.iter(){b.set_attr(NodeID(i as u32),marker,Value::Surface(SurfaceKind::Bytes,payload.clone()));
                    b.graph.insert_edge(NodeID(i as u32),branch_edge,NodeID(added),Attrs::new()).unwrap();}
            }
            let expected=size+usize::from(mutate);
            let b=branch.as_ref().unwrap();
            let writes_ok=!mutate||(b.graph.edge_count()==base_edges+targets.len()&&targets.iter().all(|&i|
                b.graph.neighbours(NodeID(i as u32),Some(branch_edge))==vec![NodeID(added.unwrap())]
                &&b.graph.node(NodeID(i as u32)).attrs.0.iter().any(|(k,val)|*k==marker
                    &&*val==Value::Surface(SurfaceKind::Bytes,payload.clone()))));
            let initial_ok=b.graph.node_count()==expected
                &&branch.as_ref().unwrap().graph.nodes_of_type(base_type).len()==size
                &&branch.as_ref().unwrap().graph.nodes_of_type(branch_type).len()==usize::from(mutate)&&writes_ok;
            if !initial_ok{v.store(false,Ordering::SeqCst);}
            r.wait();c.wait();if worker<cancel_count{drop(branch.take());}a.wait();
            if worker>=cancel_count&&mutate{let b=branch.as_ref().unwrap();let added=added.unwrap();
                let ok=targets.iter().all(|&i|b.graph.neighbours(NodeID(i as u32),Some(branch_edge))==vec![NodeID(added)]
                    &&b.graph.node(NodeID(i as u32)).attrs.0.iter().any(|(k,val)|*k==marker
                       &&*val==Value::Surface(SurfaceKind::Bytes,payload.clone())));
                if !ok{v.store(false,Ordering::SeqCst);}}
            x.wait();drop(branch);
        }));
    }
    ready.wait();let live=LIVE.load(Ordering::SeqCst);cancel.wait();after.wait();let cancelled=LIVE.load(Ordering::SeqCst);
    release.wait();for w in ws{w.join().unwrap();}
    let mut ids=Arc::try_unwrap(ids).unwrap().into_inner().unwrap();ids.sort_by_key(|x|x.0);
    let added_ids:Vec<Option<u32>>=ids.into_iter().map(|x|x.1).collect();
    let elapsed=started.elapsed().as_secs_f64()*1e6;let dropped=LIVE.load(Ordering::SeqCst);
    let primary_ok=base_intact(&primary,size,f.base_type,f.marker,f.base_edges);
    json!({"size_nodes":size,"topology":topology.name(),"write_density_percent":density,"target_policy":policy.name(),
        "target_out_degree_min_median_max_sum":degree_summary,
        "target_nodes":targets.len(),"payload_bytes":payload.len(),"fanout":fanout,"backend":backend.name(),"repeat":repeat,
        "branch_added_ids":added_ids,"cancelled_branches":cancel_count,"wall_us":elapsed,
        "baseline_live_bytes":before,"all_live_delta_bytes":live as i64-before as i64,
        "after_cancel_delta_bytes":cancelled as i64-before as i64,"after_drop_delta_bytes":dropped as i64-before as i64,
        "thread_only_control_delta_bytes":thread_control,"all_live_bytes_increased":live>before,
        "cancel_reduced_live_bytes":cancelled<live,"mutation_adjusted_after_drop_bytes":0,
        "all_semantics_pass":valid.load(Ordering::SeqCst),"primary_unchanged":primary_ok})
}

fn main(){
    fn assert_send_sync<T:Send+Sync>(){} assert_send_sync::<ExperimentSnapshot>();assert_send_sync::<Substrate>();
    let sizes=[10000usize,50000];let tops=[Topology::Path,Topology::RegularFour,Topology::Star,Topology::Grid];
    let densities=[1usize,10];let policies=[TargetPolicy::Clustered,TargetPolicy::Spread,TargetPolicy::LowDegree,TargetPolicy::HighDegree];let fanout=16usize;let repeats=3usize;
    let payload:Arc<[u8]>=vec![0x5a;128].into();let mut rows=Vec::new();
    for size in sizes{for top in tops{for density in densities{for policy in policies{for repeat in 0..repeats{
        let f=fixture(size,top);let primary=f.primary.clone();let snapshot=Arc::new(primary.snapshot().unwrap());
        let count=(size*density).div_ceil(100);let (selected,degree_summary)=select_targets(&primary,size,count,policy);let targets:Arc<Vec<usize>>=selected.into();
        let order=if repeat%2==0{[Backend::Shared,Backend::Eager]}else{[Backend::Eager,Backend::Shared]};
        for backend in order{
            let control=wave(primary.clone(),snapshot.clone(),&f,size,top,density,policy,degree_summary,fanout,backend,repeat,targets.clone(),payload.clone(),false);
            let mut measured=wave(primary.clone(),snapshot.clone(),&f,size,top,density,policy,degree_summary,fanout,backend,repeat,targets.clone(),payload.clone(),true);
            let fork_drop=control["after_drop_delta_bytes"].as_i64().unwrap();let after=measured["after_drop_delta_bytes"].as_i64().unwrap();
            let control_live=control["all_live_delta_bytes"].as_i64().unwrap();let live=measured["all_live_delta_bytes"].as_i64().unwrap();
            let control_cancel=control["after_cancel_delta_bytes"].as_i64().unwrap();let cancelled=measured["after_cancel_delta_bytes"].as_i64().unwrap();
            measured["fork_only_control_after_drop_delta_bytes"]=json!(fork_drop);
            measured["fork_only_control_all_live_delta_bytes"]=json!(control_live);
            measured["fork_only_control_after_cancel_delta_bytes"]=json!(control_cancel);
            measured["mutation_adjusted_all_live_bytes"]=json!(live-control_live);
            measured["mutation_adjusted_after_cancel_bytes"]=json!(cancelled-control_cancel);
            measured["mutation_adjusted_after_drop_bytes"]=json!(after-fork_drop);
            measured["adjusted_reclamation_pass"]=json!(after==fork_drop);
            if !measured["all_semantics_pass"].as_bool().unwrap()||!measured["primary_unchanged"].as_bool().unwrap()
                ||!measured["all_live_bytes_increased"].as_bool().unwrap()||!measured["cancel_reduced_live_bytes"].as_bool().unwrap()
                ||!measured["adjusted_reclamation_pass"].as_bool().unwrap(){panic!("lifecycle gate failed: {measured}");}
            rows.push(measured);
        }
        let later=snapshot.fork().unwrap();if !base_intact(&later,size,f.base_type,f.marker,f.base_edges){panic!("later fork changed");}
    }}}}}
    println!("{}",json!({"schema":"CowConcurrentDegreePlacementProbeV1","sizes":sizes,"topologies":["path","regular_four","star","grid"],"densities_percent":densities,"target_policies":["clustered","spread","low_out_degree","high_out_degree"],"fanout":fanout,"repeats":repeats,"rows":rows}));
}
