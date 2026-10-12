use serde::Serialize;
use std::hint::black_box;
use std::time::Instant;
use substrate_rs::cow_paged_vec::CowPagedVec;

#[derive(Serialize)]
struct Row {
    size: usize,
    fanout: usize,
    repeats: usize,
    cow_fork_batch_median_us: f64,
    vec_clone_batch_median_us: f64,
    cow_first_write_batch_median_us: f64,
    vec_first_write_batch_median_us: f64,
    cow_fork_write_batch_median_us: f64,
    vec_clone_write_batch_median_us: f64,
    cow_read_ns_per_op: f64,
    vec_read_ns_per_op: f64,
    cow_drop_batch_median_us: f64,
    vec_drop_batch_median_us: f64,
    cow_changed_pages_per_branch_median: f64,
    exact_value_and_primary_isolation: bool,
}

fn median(values: &mut [f64]) -> f64 {
    values.sort_by(f64::total_cmp);
    let n = values.len();
    if n % 2 == 0 {
        (values[n / 2 - 1] + values[n / 2]) / 2.0
    } else {
        values[n / 2]
    }
}

fn elapsed_us(start: Instant) -> f64 {
    start.elapsed().as_secs_f64() * 1_000_000.0
}

fn run(size: usize, fanout: usize, repeats: usize) -> Row {
    assert!(size > 0 && fanout > 0 && repeats > 0);
    // Base construction/publication is deliberately outside branch timings;
    // the report calls out that this prototype is not yet wired into graph
    // mutation from process start.
    let source: Vec<u64> = (0..size as u64).map(|x| x.wrapping_mul(17) + 3).collect();
    let cow_base = CowPagedVec::from_vec(source.clone());
    let mut cow_fork = Vec::new();
    let mut vec_clone = Vec::new();
    let mut cow_write = Vec::new();
    let mut vec_write = Vec::new();
    let mut cow_total = Vec::new();
    let mut vec_total = Vec::new();
    let mut cow_read = Vec::new();
    let mut vec_read = Vec::new();
    let mut cow_drop = Vec::new();
    let mut vec_drop = Vec::new();
    let mut changed_pages = Vec::new();
    let mut semantic_ok = true;

    for repetition in 0..repeats {
        let start = Instant::now();
        let mut cow_branches: Vec<_> = (0..fanout).map(|_| cow_base.fork()).collect();
        cow_fork.push(elapsed_us(start));

        let start = Instant::now();
        let mut vec_branches: Vec<_> = (0..fanout).map(|_| source.clone()).collect();
        vec_clone.push(elapsed_us(start));

        let indices: Vec<usize> = (0..fanout)
            .map(|branch| (branch * 131 + repetition * 17) % size)
            .collect();
        let start = Instant::now();
        for (branch, index) in cow_branches.iter_mut().zip(&indices) {
            let value = branch.get_mut(*index).expect("valid CowPagedVec slot");
            *value ^= 0x5a5a;
        }
        cow_write.push(elapsed_us(start));

        let start = Instant::now();
        for (branch, index) in vec_branches.iter_mut().zip(&indices) {
            branch[*index] ^= 0x5a5a;
        }
        vec_write.push(elapsed_us(start));

        let start = Instant::now();
        let mut cow_total_branches = Vec::with_capacity(fanout);
        for index in &indices {
            let mut branch = cow_base.fork();
            *branch.get_mut(*index).unwrap() ^= 0x5a5a;
            cow_total_branches.push(branch);
        }
        cow_total.push(elapsed_us(start));

        let start = Instant::now();
        let mut vec_total_branches = Vec::with_capacity(fanout);
        for index in &indices {
            let mut branch = source.clone();
            branch[*index] ^= 0x5a5a;
            vec_total_branches.push(branch);
        }
        vec_total.push(elapsed_us(start));

        let read_repetitions = 64usize;
        let start = Instant::now();
        let mut checksum = 0u64;
        for _ in 0..read_repetitions {
            for (branch, index) in cow_branches.iter().zip(&indices) {
                checksum = checksum.wrapping_add(*branch.get(*index).unwrap());
            }
        }
        black_box(checksum);
        cow_read.push(start.elapsed().as_nanos() as f64 / (read_repetitions * fanout) as f64);

        let start = Instant::now();
        let mut checksum = 0u64;
        for _ in 0..read_repetitions {
            for (branch, index) in vec_branches.iter().zip(&indices) {
                checksum = checksum.wrapping_add(branch[*index]);
            }
        }
        black_box(checksum);
        vec_read.push(start.elapsed().as_nanos() as f64 / (read_repetitions * fanout) as f64);

        let mut local_changed = 0usize;
        for (branch, index) in cow_branches.iter().zip(&indices) {
            semantic_ok &= branch.get(*index) == Some(&(source[*index] ^ 0x5a5a));
            semantic_ok &= cow_base.get(*index) == Some(&source[*index]);
            semantic_ok &= !branch.shares_page_with(&cow_base, *index);
            let untouched = if *index + 65 < size { *index + 65 } else { (*index + size - 65) % size };
            if (untouched >> 6) != (*index >> 6) {
                semantic_ok &= branch.shares_page_with(&cow_base, untouched);
            }
            local_changed += 1;
        }
        changed_pages.push(local_changed as f64 / fanout as f64);
        for index in 0..size {
            semantic_ok &= cow_base.get(index) == Some(&source[index]);
        }
        if cow_branches.len() >= 2 {
            let shared_slot = size / 2;
            let left_before = *cow_branches[0].get(shared_slot).unwrap();
            let right_before = *cow_branches[1].get(shared_slot).unwrap();
            *cow_branches[0].get_mut(shared_slot).unwrap() ^= 0x1111;
            *cow_branches[1].get_mut(shared_slot).unwrap() ^= 0x2222;
            semantic_ok &= cow_branches[0].get(shared_slot)
                == Some(&(left_before ^ 0x1111));
            semantic_ok &= cow_branches[1].get(shared_slot)
                == Some(&(right_before ^ 0x2222));
            semantic_ok &= cow_base.get(shared_slot) == Some(&source[shared_slot]);
            semantic_ok &= !cow_branches[0].shares_page_with(&cow_branches[1], shared_slot);
        }

        let start = Instant::now();
        drop(cow_branches);
        cow_drop.push(elapsed_us(start));
        let start = Instant::now();
        drop(vec_branches);
        vec_drop.push(elapsed_us(start));
        drop(cow_total_branches);
        drop(vec_total_branches);
    }

    Row {
        size,
        fanout,
        repeats,
        cow_fork_batch_median_us: median(&mut cow_fork),
        vec_clone_batch_median_us: median(&mut vec_clone),
        cow_first_write_batch_median_us: median(&mut cow_write),
        vec_first_write_batch_median_us: median(&mut vec_write),
        cow_fork_write_batch_median_us: median(&mut cow_total),
        vec_clone_write_batch_median_us: median(&mut vec_total),
        cow_read_ns_per_op: median(&mut cow_read),
        vec_read_ns_per_op: median(&mut vec_read),
        cow_drop_batch_median_us: median(&mut cow_drop),
        vec_drop_batch_median_us: median(&mut vec_drop),
        cow_changed_pages_per_branch_median: median(&mut changed_pages),
        exact_value_and_primary_isolation: semantic_ok,
    }
}

fn main() {
    let mut sizes = vec![771usize, 1_771, 10_771, 50_771];
    let mut fanouts = vec![1usize, 2, 4, 8, 32];
    let mut repeats = 25usize;
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--sizes" => sizes = args.next().expect("--sizes value").split(',').map(|x| x.parse().unwrap()).collect(),
            "--fanouts" => fanouts = args.next().expect("--fanouts value").split(',').map(|x| x.parse().unwrap()).collect(),
            "--repeats" => repeats = args.next().expect("--repeats value").parse().unwrap(),
            other => panic!("unknown argument: {other}"),
        }
    }
    let rows: Vec<Row> = sizes.into_iter()
        .flat_map(|size| fanouts.iter().copied().map(move |fanout| run(size, fanout, repeats)))
        .collect();
    println!("{}", serde_json::to_string(&rows).unwrap());
}
