//! Performance test Jabberwock proposed in
//! `scripts/jabberwock_proposes_perf_test.py`.
//!
//! Run with:
//!   cd runners/dsl
//!   RUSTFLAGS="-C target-cpu=native" cargo run --release \
//!       --example jabberwock_perf_test
//!
//! Three microbenchmarks pitting specific Jabberwock-design predictions
//! (from the hardware-aware design commit bc4fe5f) against measured
//! reality on whatever system this is run on.

use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};

use rustc_hash::FxHashMap;
use substrate_rs::checker::ConsistencyChecker;
use substrate_rs::code_cache::CodeCacheConfig;
use substrate_rs::grammar::Grammar;
use substrate_rs::l2_adaptive::{AdaptiveDispatcher, TierUpPolicy, TypedTask};
use substrate_rs::l2_dispatch::{PriorityClass, Scheduler, Task};
use substrate_rs::l2_dispatch_work_stealing::WorkStealingScheduler;
use substrate_rs::l3_drives::KalmanFilter1D;
use substrate_rs::l3_kalman_nd::KalmanFilterND;
use substrate_rs::l3_lqr::Mat;
use substrate_rs::substrate::Substrate;
use substrate_rs::value::Value;

/// Format throughput in human-readable units.
fn fmt_per_sec(n: f64) -> String {
    if n >= 1e9 {
        format!("{:.2} G/s", n / 1e9)
    } else if n >= 1e6 {
        format!("{:.2} M/s", n / 1e6)
    } else if n >= 1e3 {
        format!("{:.2} K/s", n / 1e3)
    } else {
        format!("{:.2} /s", n)
    }
}

fn print_section(title: &str) {
    println!();
    println!("{}", "=".repeat(72));
    println!("{}", title);
    println!("{}", "=".repeat(72));
}

fn print_result(prediction_per_sec: f64, measured_per_sec: f64) {
    let ratio = measured_per_sec / prediction_per_sec;
    let verdict = if ratio >= 1.0 { "BEAT" } else { "MISS" };
    println!(
        "  Prediction: {} | Measured: {} | Ratio: {:.2}× | {}",
        fmt_per_sec(prediction_per_sec),
        fmt_per_sec(measured_per_sec),
        ratio,
        verdict
    );
}

// =======================================================================
// Benchmark 1: Graph mutation throughput
// =======================================================================

fn bench_graph_mutations() {
    print_section("Benchmark 1: Graph mutation throughput");
    println!("  Prediction: ~30M node mutations/sec sustained");
    println!();
    let n: usize = 1_000_000;
    let mut s = Substrate::new(ConsistencyChecker::new(Grammar::new()));
    let type_sym = s.interner.intern("BenchNode");

    // Warm: 10K inserts so the arena resizes once + JIT warm.
    for _ in 0..10_000 {
        s.add_node(type_sym, FxHashMap::default());
    }

    // Measurement.
    let start = Instant::now();
    for _ in 0..n {
        s.add_node(type_sym, FxHashMap::default());
    }
    let elapsed = start.elapsed();
    let rate = n as f64 / elapsed.as_secs_f64();
    println!(
        "  Inserted {} nodes in {:?} ({:.3} s)",
        n,
        elapsed,
        elapsed.as_secs_f64()
    );
    println!("  Throughput: {}", fmt_per_sec(rate));
    print_result(30e6, rate);
}

// =======================================================================
// Benchmark 2: L2 dispatcher submit throughput
// =======================================================================

fn bench_dispatcher_submit() {
    print_section("Benchmark 2: L2 dispatcher submit throughput");
    println!("  Prediction: ~100M reflex-firings/sec across 6 workers");
    println!("  (no-op submit measures dispatcher overhead; actual");
    println!("   reflex-firing rate is bounded by reflex work)");
    println!();

    let n: usize = 100_000;
    let sched = Scheduler::new(6);

    let counter = Arc::new(AtomicUsize::new(0));
    let start = Instant::now();
    for _ in 0..n {
        let c = Arc::clone(&counter);
        sched.submit(Task {
            deadline: Instant::now() + Duration::from_secs(60),
            class: PriorityClass::BestEffort,
            work: Box::new(move || {
                c.fetch_add(1, Ordering::Relaxed);
            }),
        });
    }
    // Wait until all tasks complete.
    while counter.load(Ordering::Relaxed) < n {
        std::thread::sleep(Duration::from_micros(100));
    }
    let elapsed = start.elapsed();
    let rate = n as f64 / elapsed.as_secs_f64();
    sched.drain_and_shutdown();
    println!(
        "  Submitted {} no-op tasks across 6 workers in {:?}",
        n, elapsed
    );
    println!("  Throughput: {}", fmt_per_sec(rate));
    print_result(100e6, rate);
}

// =======================================================================
// Benchmark 3: 1D Kalman update throughput
// =======================================================================

fn bench_kalman_updates() {
    print_section("Benchmark 3: 1D Kalman update throughput");
    println!("  Prediction: ~250K state updates/sec single-core (≤ 64 dim)");
    println!("  (1D case should beat the ≤64-dim prediction)");
    println!();
    let n: usize = 1_000_000;
    let mut kf = KalmanFilter1D::new(0.0, 100.0, 0.01, 1.0);

    // Warm.
    for _ in 0..10_000 {
        kf.update(1.0);
    }

    let start = Instant::now();
    let mut acc = 0.0_f64;
    for i in 0..n {
        let measurement = 7.0 + ((i as f64 * 0.001).sin());
        let inn = kf.update(measurement);
        acc += inn.raw;
    }
    let elapsed = start.elapsed();
    let rate = n as f64 / elapsed.as_secs_f64();
    println!(
        "  {} 1D Kalman updates in {:?} ({:.3} s)",
        n,
        elapsed,
        elapsed.as_secs_f64()
    );
    println!(
        "  Throughput: {}  (acc={:.6}, final x_hat={:.6})",
        fmt_per_sec(rate),
        acc,
        kf.x_hat
    );
    print_result(250e3, rate);
}

// =======================================================================
// Benchmark 2b: Work-stealing scheduler submit throughput
// =======================================================================

fn bench_work_stealing_submit() {
    print_section("Benchmark 2b: Work-stealing scheduler submit throughput");
    println!("  Same workload as Bench 2 but on the lock-free");
    println!("  WorkStealingScheduler (crossbeam-deque Injector +");
    println!("  per-worker FIFO + cross-worker stealing).");
    println!("  Prediction: ~100M reflex-firings/sec across 6 workers");
    println!();

    let n: usize = 100_000;
    let sched = WorkStealingScheduler::new(6);
    let counter = Arc::new(AtomicUsize::new(0));
    let start = Instant::now();
    for _ in 0..n {
        let c = Arc::clone(&counter);
        sched.submit(move || {
            c.fetch_add(1, Ordering::Relaxed);
        });
    }
    while counter.load(Ordering::Relaxed) < n {
        std::thread::sleep(Duration::from_micros(100));
    }
    let elapsed = start.elapsed();
    let rate = n as f64 / elapsed.as_secs_f64();
    sched.shutdown();
    println!(
        "  Submitted {} no-op tasks across 6 workers in {:?}",
        n, elapsed
    );
    println!("  Throughput: {}", fmt_per_sec(rate));
    print_result(100e6, rate);
}

// =======================================================================
// Benchmark 3b: 4-dim Kalman update throughput
// Benchmark 3c: 16-dim Kalman update throughput
// =======================================================================

fn build_kalman(dim: usize) -> KalmanFilterND {
    let x0 = {
        let mut m = Mat::zeros(dim, 1);
        for i in 0..dim {
            m.set(i, 0, 0.0);
        }
        m
    };
    let mut p0 = Mat::identity(dim);
    for i in 0..dim {
        p0.set(i, i, 100.0);
    }
    let a = Mat::identity(dim); // identity dynamics
    let c = Mat::identity(dim); // observe all
    let mut q = Mat::zeros(dim, dim);
    for i in 0..dim {
        q.set(i, i, 0.01);
    }
    let mut r = Mat::zeros(dim, dim);
    for i in 0..dim {
        r.set(i, i, 1.0);
    }
    KalmanFilterND::new(x0, p0, a, None, c, q, r).expect("KF construct")
}

fn bench_kalman_nd(dim: usize, n: usize) {
    print_section(&format!(
        "Benchmark 3{}: {}-dim Kalman update throughput (FP64)",
        if dim == 4 { "b" } else { "c" },
        dim
    ));
    println!("  Prediction was ~250K updates/sec for ≤64-dim case");
    println!("  (single-core); this is the proper test.");
    println!();
    let mut kf = build_kalman(dim);
    let meas_warm = {
        let mut m = Mat::zeros(dim, 1);
        for i in 0..dim {
            m.set(i, 0, (i as f64) * 0.1);
        }
        m
    };
    for _ in 0..100 {
        kf.predict(None).unwrap();
        kf.update(&meas_warm).unwrap();
    }
    let measurements: Vec<Mat> = (0..16)
        .map(|k| {
            let mut m = Mat::zeros(dim, 1);
            for i in 0..dim {
                m.set(i, 0, (i as f64) + 0.1 * (k as f64).sin());
            }
            m
        })
        .collect();
    let start = Instant::now();
    for k in 0..n {
        kf.predict(None).unwrap();
        kf.update(&measurements[k & 15]).unwrap();
    }
    let elapsed = start.elapsed();
    let rate = n as f64 / elapsed.as_secs_f64();
    println!(
        "  {} updates in {:?} ({:.3} s)",
        n,
        elapsed,
        elapsed.as_secs_f64()
    );
    println!("  Throughput: {}", fmt_per_sec(rate));
    print_result(250e3, rate);
}

fn bench_kalman_nd_bf16_cached(dim: usize, n: usize) {
    print_section(&format!(
        "Benchmark 3{}-BF16-CACHED: {}-dim Kalman (BF16 matmul w/ caches)",
        if dim == 16 { "c" } else { "d" },
        dim
    ));
    println!("  Same as the uncached BF16 path but pre-packs C, C^T");
    println!("  once + P once per update. Amortises 5 of 6 matmul");
    println!("  conversions per update.");
    println!();
    let mut kf = build_kalman(dim);
    kf.build_bf16_caches();
    let meas_warm = {
        let mut m = Mat::zeros(dim, 1);
        for i in 0..dim {
            m.set(i, 0, (i as f64) * 0.1);
        }
        m
    };
    for _ in 0..100 {
        kf.predict_bf16(None).unwrap();
        kf.update_bf16_cached(&meas_warm).unwrap();
    }
    let measurements: Vec<Mat> = (0..16)
        .map(|k| {
            let mut m = Mat::zeros(dim, 1);
            for i in 0..dim {
                m.set(i, 0, (i as f64) + 0.1 * (k as f64).sin());
            }
            m
        })
        .collect();
    let start = Instant::now();
    for k in 0..n {
        kf.predict_bf16(None).unwrap();
        kf.update_bf16_cached(&measurements[k & 15]).unwrap();
    }
    let elapsed = start.elapsed();
    let rate = n as f64 / elapsed.as_secs_f64();
    println!(
        "  {} updates in {:?} ({:.3} s)",
        n,
        elapsed,
        elapsed.as_secs_f64()
    );
    println!("  Throughput: {}", fmt_per_sec(rate));
    print_result(250e3, rate);
}

fn bench_kalman_nd_bf16(dim: usize, n: usize) {
    print_section(&format!(
        "Benchmark 3{}-BF16: {}-dim Kalman update (AVX-512 BF16 matmul)",
        if dim == 16 { "c" } else { "d" },
        dim
    ));
    println!("  Same Kalman, but BF16 matmul for the heavy covariance");
    println!("  updates. Matrix inverse stays FP64 for precision.");
    println!();
    let mut kf = build_kalman(dim);
    let meas_warm = {
        let mut m = Mat::zeros(dim, 1);
        for i in 0..dim {
            m.set(i, 0, (i as f64) * 0.1);
        }
        m
    };
    for _ in 0..100 {
        kf.predict_bf16(None).unwrap();
        kf.update_bf16(&meas_warm).unwrap();
    }
    let measurements: Vec<Mat> = (0..16)
        .map(|k| {
            let mut m = Mat::zeros(dim, 1);
            for i in 0..dim {
                m.set(i, 0, (i as f64) + 0.1 * (k as f64).sin());
            }
            m
        })
        .collect();
    let start = Instant::now();
    for k in 0..n {
        kf.predict_bf16(None).unwrap();
        kf.update_bf16(&measurements[k & 15]).unwrap();
    }
    let elapsed = start.elapsed();
    let rate = n as f64 / elapsed.as_secs_f64();
    println!(
        "  {} updates in {:?} ({:.3} s)",
        n,
        elapsed,
        elapsed.as_secs_f64()
    );
    println!("  Throughput: {}", fmt_per_sec(rate));
    print_result(250e3, rate);
}

// =======================================================================
// Benchmark 5: Raw 64×64 matmul — FP64 vs BF16 (isolated)
// =======================================================================

fn bench_raw_matmul_64(iters: usize) {
    print_section("Benchmark 5: Raw 64×64 matmul throughput (FP64 vs BF16)");
    println!("  Isolates matmul cost from Kalman integration overhead.");
    println!("  Same matrices reused across iterations — measures the");
    println!("  matmul path itself, not the per-call conversion.");
    println!();
    let n = 64;
    let mut a = Mat::zeros(n, n);
    let mut b = Mat::zeros(n, n);
    for i in 0..n {
        for j in 0..n {
            a.set(i, j, ((i * 31 + j * 17) % 23) as f64 * 0.1);
            b.set(i, j, ((i * 11 + j * 41) % 19) as f64 * 0.05);
        }
    }

    // Warm.
    for _ in 0..10 {
        let _ = a.mul(&b);
    }

    // FP64 path.
    let start = Instant::now();
    let mut acc = 0.0_f64;
    for _ in 0..iters {
        let c = a.mul(&b);
        acc += c.get(0, 0);
    }
    let elapsed_fp64 = start.elapsed();
    let rate_fp64 = iters as f64 / elapsed_fp64.as_secs_f64();
    println!(
        "  FP64 (AVX-512):  {} ({:?}, acc={:.6})",
        fmt_per_sec(rate_fp64),
        elapsed_fp64,
        acc
    );

    // BF16 path.
    for _ in 0..10 {
        let _ = a.mul_bf16(&b);
    }
    let start = Instant::now();
    let mut acc = 0.0_f64;
    for _ in 0..iters {
        let c = a.mul_bf16(&b);
        acc += c.get(0, 0);
    }
    let elapsed_bf16 = start.elapsed();
    let rate_bf16 = iters as f64 / elapsed_bf16.as_secs_f64();
    println!(
        "  BF16 (AVX-512_BF16): {} ({:?}, acc={:.6})",
        fmt_per_sec(rate_bf16),
        elapsed_bf16,
        acc
    );

    println!();
    println!("  BF16 / FP64 speedup: {:.2}×", rate_bf16 / rate_fp64);
}

// =======================================================================
// Benchmark 4 (bonus): AdaptiveDispatcher typed-submit
// =======================================================================

fn bench_adaptive_dispatcher_typed_submit() {
    print_section("Benchmark 4 (bonus): AdaptiveDispatcher typed submit");
    println!("  No specific prediction; measures the L2-dynamic surface's");
    println!("  per-submit overhead including hot-counter update +");
    println!("  classification.");
    println!();
    let s = Substrate::new(ConsistencyChecker::new(Grammar::new()));
    let dispatcher: AdaptiveDispatcher<crate::FakeJit> = AdaptiveDispatcher::with_shared_epoch(
        Scheduler::new(6),
        TierUpPolicy {
            threshold: u64::MAX,
            cooling_threshold: 3,
        },
        CodeCacheConfig::default(),
        s.gamma_epoch(),
    );
    let n: usize = 100_000;
    let mut interner = s.interner;
    let kind = interner.intern("bench_kind");
    let counter = Arc::new(AtomicUsize::new(0));
    let start = Instant::now();
    for _ in 0..n {
        let c = Arc::clone(&counter);
        let _ = dispatcher.submit(TypedTask {
            kind,
            deadline: Instant::now() + Duration::from_secs(60),
            class: PriorityClass::BestEffort,
            work: Box::new(move || {
                c.fetch_add(1, Ordering::Relaxed);
            }),
        });
    }
    while counter.load(Ordering::Relaxed) < n {
        std::thread::sleep(Duration::from_micros(100));
    }
    let elapsed = start.elapsed();
    let rate = n as f64 / elapsed.as_secs_f64();
    dispatcher.drain_and_shutdown();
    println!(
        "  Submitted {} typed tasks across 6 workers in {:?}",
        n, elapsed
    );
    println!("  Throughput: {}", fmt_per_sec(rate));
}

// FakeJit payload — just need something that impls CodeSize.
struct FakeJit;
impl substrate_rs::code_cache::CodeSize for FakeJit {
    fn code_size_bytes(&self) -> usize {
        0
    }
}

fn main() {
    println!();
    println!("{}", "#".repeat(72));
    println!("#  JABBERWOCK'S PROPOSED PERFORMANCE TEST");
    println!("#  Target: Ryzen 9600X + AVX-512 + 32 MiB L3 (per commit bc4fe5f)");
    println!("{}", "#".repeat(72));
    bench_graph_mutations();
    bench_dispatcher_submit();
    bench_work_stealing_submit();
    bench_kalman_updates();
    bench_kalman_nd(4, 200_000);
    bench_kalman_nd(16, 50_000);
    bench_kalman_nd_bf16(16, 50_000);
    bench_kalman_nd_bf16_cached(16, 50_000);
    bench_kalman_nd(64, 5_000);
    bench_kalman_nd_bf16(64, 5_000);
    bench_kalman_nd_bf16_cached(64, 10_000);
    bench_raw_matmul_64(5_000);
    bench_adaptive_dispatcher_typed_submit();
    println!();
    println!("{}", "=".repeat(72));
    println!("Summary: see per-bench BEAT/MISS verdicts above.");
    println!("{}", "=".repeat(72));
    println!();
}
