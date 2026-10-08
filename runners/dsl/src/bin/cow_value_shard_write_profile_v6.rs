use roaring::RoaringBitmap;
use std::env;
use std::fs;
use std::hint::black_box;
use std::time::Instant;
use substrate_rs::cow_sharded_map::CowShardedMap;
use substrate_rs::value::Value;

fn rss_kb() -> (u64, u64) {
    let status = fs::read_to_string("/proc/self/status").unwrap_or_default();
    let value = |name: &str| -> u64 {
        status
            .lines()
            .find(|line| line.starts_with(name))
            .and_then(|line| line.split_whitespace().nth(1))
            .and_then(|v| v.parse().ok())
            .unwrap_or(0)
    };
    (value("VmRSS:"), value("VmHWM:"))
}

fn run<const S: usize>(n: usize, reps: usize, arm: &str) {
    let before = rss_kb();
    let mut map: CowShardedMap<Value, RoaringBitmap, S> = CowShardedMap::default();
    for i in 0..n {
        let mut bitmap = RoaringBitmap::new();
        bitmap.insert(i as u32);
        map.insert(Value::Int(i as i64), bitmap);
    }
    let after_fixture = rss_kb();
    let lengths = map.shard_lengths();
    let key = Value::Int((n / 2) as i64);
    let probe = map.clone();
    let (root_refs, copied_entries) = probe.shared_write_copy_estimate(&key);
    drop(probe);
    let mut fork_ns = Vec::with_capacity(reps);
    let mut write_ns = Vec::with_capacity(reps);
    let mut total_ns = Vec::with_capacity(reps);
    for _ in 0..reps {
        let sibling = map.clone();
        let t = Instant::now();
        let mut branch = if arm == "cow" {
            map.clone()
        } else {
            map.deep_copy()
        };
        let fork = t.elapsed().as_nanos();
        let w = Instant::now();
        let removed = branch.remove(&key).expect("selected key exists");
        assert_eq!(removed.len(), 1);
        assert!(!branch.contains_key(&key));
        assert!(map.contains_key(&key));
        assert!(sibling.contains_key(&key));
        black_box(&branch);
        let write = w.elapsed().as_nanos();
        fork_ns.push(fork);
        write_ns.push(write);
        total_ns.push(fork + write);
    }
    let after = rss_kb();
    println!("{{\"n\":{n},\"shards\":{S},\"reps\":{reps},\"arm\":\"{arm}\",\"fork_ns\":{fork_ns:?},\"write_ns\":{write_ns:?},\"total_ns\":{total_ns:?},\"root_refs_copied\":{root_refs},\"selected_shard_entries\":{copied_entries},\"shard_lengths\":{lengths:?},\"rss_before_kb\":{},\"rss_fixture_kb\":{},\"rss_after_kb\":{},\"hwm_kb\":{}}}", before.0, after_fixture.0, after.0, after.1);
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let n: usize = args[1].parse().unwrap();
    let shards: usize = args[2].parse().unwrap();
    let reps: usize = args[3].parse().unwrap();
    let arm = &args[4];
    match shards {
        64 => run::<64>(n, reps, arm),
        128 => run::<128>(n, reps, arm),
        256 => run::<256>(n, reps, arm),
        512 => run::<512>(n, reps, arm),
        _ => panic!("unsupported shard count"),
    }
}
