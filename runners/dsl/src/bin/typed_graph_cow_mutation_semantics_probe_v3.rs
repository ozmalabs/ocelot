use serde::Serialize;
use substrate_rs::graph::{Attrs, NodeID, TypedGraph};
use substrate_rs::sym::Sym;
use substrate_rs::value::Value;

#[derive(Clone, Copy)]
enum Backend { Eager, SharedRecords, SharedGraphPages }
impl Backend {
    const ALL: [Self; 3] = [Self::Eager, Self::SharedRecords, Self::SharedGraphPages];
    fn name(self) -> &'static str { match self { Self::Eager => "eager", Self::SharedRecords => "shared_records", Self::SharedGraphPages => "shared_graph_pages" } }
    fn fork(self, g: &TypedGraph) -> TypedGraph { match self { Self::Eager => g.clone_eager(), Self::SharedRecords => g.clone_sharing_slabs(), Self::SharedGraphPages => g.clone_sharing_graph_pages() } }
}
#[derive(Clone, Copy)]
enum Topology { Path, StarAugmented, GridAugmented }
impl Topology { const ALL: [Self;3]=[Self::Path,Self::StarAugmented,Self::GridAugmented]; fn name(self)->&'static str { match self {Self::Path=>"path",Self::StarAugmented=>"star_augmented",Self::GridAugmented=>"grid_augmented"} } }
#[derive(Serialize)]
struct Row { nodes: usize, topology: &'static str, schedule: usize, backend: &'static str, primary_unchanged: bool, fork_matches_eager: bool, nested_matches_eager: bool, sibling_isolated: bool, delete_append_id_reuse: bool, derived_indexes_match_eager: bool }

fn graph(nodes: usize, topology: Topology) -> TypedGraph {
    let mut g=TypedGraph::new();
    for i in 0..nodes { let mut a=Attrs::new(); a.insert(Sym(3),Value::Int(i as i64)); a.insert(Sym(4),Value::Bool(i%2==0)); g.insert_node(Sym(1),a); }
    for i in 0..nodes-1 { g.insert_edge(NodeID(i as u32),Sym(2),NodeID((i+1) as u32),Attrs::new()).unwrap(); }
    match topology {
        Topology::Path=>{},
        Topology::StarAugmented=>for i in 1..nodes { g.insert_edge(NodeID(0),Sym(5),NodeID(i as u32),Attrs::new()).unwrap(); },
        Topology::GridAugmented=>{ let cols=(nodes as f64).sqrt().ceil() as usize; for i in 0..nodes { let row=i/cols; let col=i%cols; if col+1<cols && i+1<nodes {g.insert_edge(NodeID(i as u32),Sym(5),NodeID((i+1) as u32),Attrs::new()).unwrap();} let down=i+cols; if row+1<nodes.div_ceil(cols) && down<nodes {g.insert_edge(NodeID(i as u32),Sym(5),NodeID(down as u32),Attrs::new()).unwrap();} } }
    }
    for (ty,key) in [(Sym(1),Sym(3)),(Sym(4),Sym(3)),(Sym(1),Sym(4)),(Sym(4),Sym(4))] { g.declare_attr_index(ty,key); }
    g
}
fn signature(g:&TypedGraph)->String {
    let mut rows=Vec::new();
    for nid in g.all_nodes() { let n=g.node(nid); let mut es=Vec::new(); for et in [Sym(2),Sym(5)] { for idx in g.out_edges_idx(nid,Some(et)) {let e=g.edge(idx); es.push(format!("{}:{}:{}:{:?}",e.src.0,e.edge_type.0,e.tgt.0,g.edge_attrs(idx)));} } rows.push(format!("n{}:{}:{:?}:{}",nid.0,n.type_.0,n.attrs,es.join(","))); }
    rows.join("|")
}
fn query_signature(g:&TypedGraph)->String {
    let mut q=Vec::new();
    for (ty,key,value) in [(Sym(1),Sym(3),Value::Int(20)),(Sym(1),Sym(3),Value::Int(-20)),(Sym(4),Sym(3),Value::Int(22)),(Sym(1),Sym(4),Value::Bool(true)),(Sym(1),Sym(4),Value::Bool(false)),(Sym(4),Sym(4),Value::Bool(true))] {q.push(format!("where:{}:{}:{:?}:{:?}",ty.0,key.0,value,g.nodes_where(ty,key,&value)));}
    for ty in [Sym(1),Sym(4),Sym(6),Sym(7)] {q.push(format!("type:{}:{:?}",ty.0,g.nodes_of_type(ty)));}
    for et in [Sym(2),Sym(5)] {let es:Vec<_>=g.edges_by_type(et).iter().map(|idx|{let e=g.edge(*idx);format!("{}:{}:{}:{:?}",e.src.0,e.edge_type.0,e.tgt.0,g.edge_attrs(*idx))}).collect();q.push(format!("edge_type:{}:{}",et.0,es.join(",")));}
    for nid in [NodeID(0),NodeID(10),NodeID(22),NodeID(30),NodeID(40)] {q.push(format!("adj:{}:out={:?}:in={:?}",nid.0,g.neighbours(nid,None),g.in_neighbours(nid,None)));}
    q.join("|")
}
fn attr_changes(g:&mut TypedGraph) {g.set_node_attr(NodeID(20),Sym(3),Value::Int(-20));g.set_node_attr(NodeID(20),Sym(4),Value::Bool(false));g.remove_node_attr(NodeID(21),Sym(4));}
fn retype(g:&mut TypedGraph) {g.set_node_type(NodeID(22),Sym(4));}
fn edge_changes(g:&mut TypedGraph) {let idx=g.edge_idx(NodeID(12),Sym(2),NodeID(13)).unwrap();g.edge_attrs_mut(idx).insert(Sym(8),Value::Int(808));let idx=g.edge_idx(NodeID(10),Sym(2),NodeID(11)).unwrap();g.delete_edge(idx);}
fn delete_reuse_append(g:&mut TypedGraph)->bool {let deleted=NodeID(30);let ok=g.delete_node(deleted).is_some();let recycled=g.insert_node(Sym(1),Attrs::new());let edge_ok=g.insert_edge(recycled,Sym(5),NodeID(40),Attrs::new()).is_ok();ok&&edge_ok&&recycled==deleted&&!g.has_edge(NodeID(29),Sym(2),deleted)}
fn mutate(g:&mut TypedGraph,schedule:usize)->bool {match schedule {0=>{attr_changes(g);retype(g);edge_changes(g);delete_reuse_append(g)},1=>{edge_changes(g);retype(g);attr_changes(g);delete_reuse_append(g)},2=>{let ok=delete_reuse_append(g);edge_changes(g);attr_changes(g);retype(g);ok},_=>false}}
fn run(nodes:usize,topology:Topology,schedule:usize)->Vec<Row> {
    let base=graph(nodes,topology);let base_state=signature(&base);let base_queries=query_signature(&base);
    let mut branches:Vec<_>=Backend::ALL.iter().map(|b|{let mut x=b.fork(&base);assert!(mutate(&mut x,schedule));x}).collect();
    let eager_state=signature(&branches[0]);let eager_queries=query_signature(&branches[0]);let mut rows=Vec::new();
    for (i,b) in Backend::ALL.iter().copied().enumerate() {
        let fork_matches_eager=signature(&branches[i])==eager_state&&query_signature(&branches[i])==eager_queries&&branches[i].node_count()==branches[0].node_count()&&branches[i].edge_count()==branches[0].edge_count();
        let primary_unchanged=signature(&base)==base_state&&query_signature(&base)==base_queries;
        let mut nested=b.fork(&branches[i]);nested.set_node_type(NodeID(40),Sym(6));nested.insert_edge(NodeID(41),Sym(5),NodeID(42),Attrs::new()).unwrap();
        let mut eager_nested=Backend::Eager.fork(&branches[0]);eager_nested.set_node_type(NodeID(40),Sym(6));eager_nested.insert_edge(NodeID(41),Sym(5),NodeID(42),Attrs::new()).unwrap();
        let nested_matches_eager=signature(&nested)==signature(&eager_nested)&&query_signature(&nested)==query_signature(&eager_nested);
        let mut sibling=b.fork(&branches[i]);sibling.set_node_type(NodeID(40),Sym(7));
        let mut eager_sibling=Backend::Eager.fork(&branches[0]);eager_sibling.set_node_type(NodeID(40),Sym(7));
        let derived_indexes_match_eager=fork_matches_eager&&query_signature(&nested)==query_signature(&eager_nested)&&query_signature(&sibling)==query_signature(&eager_sibling);
        let sibling_isolated=signature(&branches[i])==eager_state&&signature(&sibling)!=eager_state&&signature(&base)==base_state&&signature(&nested)==signature(&eager_nested);
        rows.push(Row{nodes,topology:topology.name(),schedule,backend:b.name(),primary_unchanged,fork_matches_eager,nested_matches_eager,sibling_isolated,delete_append_id_reuse:branches[i].has_node(NodeID(30))&&branches[i].node(NodeID(30)).type_==Sym(1)&&!branches[i].has_edge(NodeID(29),Sym(2),NodeID(30)),derived_indexes_match_eager});
    } rows
}
fn main(){let sizes:Vec<usize>=std::env::args().nth(1).unwrap_or_else(||"771,10771,50771".into()).split(',').map(|x|x.parse().unwrap()).collect();let rows:Vec<Row>=sizes.into_iter().flat_map(|n|Topology::ALL.into_iter().flat_map(move|t|(0..3).flat_map(move|s|run(n,t,s)))).collect();println!("{}",serde_json::to_string(&rows).unwrap());}
