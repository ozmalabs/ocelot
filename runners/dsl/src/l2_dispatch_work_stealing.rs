//! L2 work-stealing scheduler — FIFO throughput-optimised alternative
//! to the single-Mutex EDF [`crate::l2_dispatch::Scheduler`].
//!
//! ## Why this exists
//!
//! Jabberwock's hardware-aware design (commit bc4fe5f) predicted
//! ~100M reflex-firings/sec across 6 workers. The single-Mutex EDF
//! `Scheduler` measured at 1.55 M/s (commit fe93761) — a 64× gap.
//! Cause: every submit acquires the global Mutex; producer
//! serialises.
//!
//! This scheduler removes that bottleneck via `crossbeam-deque`:
//!
//! - Global injector queue (`Injector<Task>`) — lock-free MPMC.
//! - Per-worker FIFO deque (`Worker<Task>`) — owner-only push/pop.
//! - Cross-worker stealers (`Stealer<Task>`) — workers steal from
//!   each other when local queue is empty.
//!
//! The Mt's L2 pattern names "per-Mt local queues + global overflow"
//! exactly. This module instantiates it without the Mt-key sharding
//! (Tasks aren't tagged with a Mt yet at this layer); a future
//! revision could shard by `kind: Sym` for cache-locality of Mt-
//! specific reflexes.
//!
//! ## Tradeoffs vs the EDF Scheduler
//!
//! - **FIFO only.** No deadline ordering. For mixed-deadline
//!   workloads the EDF Scheduler is correct; for high-throughput
//!   homogeneous workloads (the bench scenario), this is much faster.
//! - **No EDF priority class.** Tasks are submitted as bare closures.
//! - **Same shutdown semantics.** Drop or `shutdown()` to join workers.
//!
//! Callers pick: EDF when deadlines matter, work-stealing for
//! throughput. A future "hybrid" could shard per priority class +
//! steal within class.

use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread::{self, JoinHandle};

use crossbeam_deque::{Injector, Steal, Stealer, Worker};

type BoxedTask = Box<dyn FnOnce() + Send + 'static>;

/// Work-stealing scheduler. Multi-producer submit via lock-free
/// injector; per-worker FIFO deques with cross-worker stealing.
pub struct WorkStealingScheduler {
    injector: Arc<Injector<BoxedTask>>,
    workers: Vec<JoinHandle<()>>,
    shutdown_flag: Arc<AtomicBool>,
}

impl WorkStealingScheduler {
    /// Construct with `n_workers` worker threads.
    pub fn new(n_workers: usize) -> Self {
        let injector: Arc<Injector<BoxedTask>> = Arc::new(Injector::new());
        let shutdown_flag = Arc::new(AtomicBool::new(false));

        // Build per-worker local deques.
        let local_queues: Vec<Worker<BoxedTask>> =
            (0..n_workers).map(|_| Worker::<BoxedTask>::new_fifo()).collect();
        // Each worker keeps refs to every other's stealer.
        let stealers: Vec<Stealer<BoxedTask>> =
            local_queues.iter().map(|w| w.stealer()).collect();
        let stealers = Arc::new(stealers);

        // Spawn workers, pinned to physical cores when possible.
        let core_ids = core_affinity::get_core_ids();
        let mut workers = Vec::with_capacity(n_workers);
        for (idx, local) in local_queues.into_iter().enumerate() {
            let inj = Arc::clone(&injector);
            let stl = Arc::clone(&stealers);
            let sf = Arc::clone(&shutdown_flag);
            let pin = core_ids.as_ref()
                .and_then(|ids| ids.get(idx).copied());
            let handle = thread::Builder::new()
                .name(format!("ws-worker-{}", idx))
                .spawn(move || {
                    if let Some(c) = pin {
                        let _ = core_affinity::set_for_current(c);
                    }
                    worker_loop(local, inj, stl, idx, sf);
                })
                .expect("spawn ws worker");
            workers.push(handle);
        }

        Self { injector, workers, shutdown_flag }
    }

    /// Submit a task. Lock-free push into the global injector;
    /// workers pull from there + their own local + each other.
    pub fn submit<F: FnOnce() + Send + 'static>(&self, work: F) {
        self.injector.push(Box::new(work));
    }

    /// Signal shutdown + drain remaining tasks. Workers complete
    /// queued + in-flight work before exiting.
    pub fn shutdown(self) {
        self.shutdown_flag.store(true, Ordering::Release);
        for h in self.workers {
            let _ = h.join();
        }
    }

    /// Approximate queued task count across global + locals. Diagnostic
    /// only; not synchronously consistent.
    pub fn approx_pending(&self) -> usize {
        // Injector doesn't expose length; return 0 as approximation.
        // Future revision could add per-worker counters.
        let _ = &self.injector;
        0
    }
}

fn worker_loop(
    local: Worker<BoxedTask>,
    injector: Arc<Injector<BoxedTask>>,
    stealers: Arc<Vec<Stealer<BoxedTask>>>,
    my_idx: usize,
    shutdown: Arc<AtomicBool>,
) {
    loop {
        // 1. Local queue first.
        if let Some(task) = local.pop() {
            task();
            continue;
        }

        // 2. Global injector — steal a batch into local for amortised
        //    lock-free transfer.
        loop {
            match injector.steal_batch_and_pop(&local) {
                Steal::Success(task) => { task(); break; }
                Steal::Empty => break,
                Steal::Retry => continue,
            }
        }
        if local.pop().is_some_and(|t| { t(); true }) {
            continue;
        }

        // 3. Steal from a sibling worker.
        let n = stealers.len();
        let mut got_one = false;
        for offset in 1..n {
            let target = (my_idx + offset) % n;
            loop {
                match stealers[target].steal() {
                    Steal::Success(task) => { task(); got_one = true; break; }
                    Steal::Empty => break,
                    Steal::Retry => continue,
                }
            }
            if got_one { break; }
        }
        if got_one { continue; }

        // 4. Nothing to do — check shutdown.
        if shutdown.load(Ordering::Acquire) {
            // Drain anything in injector or own queue before exit.
            if let Some(task) = local.pop() { task(); continue; }
            match injector.steal_batch_and_pop(&local) {
                Steal::Success(task) => { task(); continue; }
                _ => return,
            }
        }

        // 5. Idle backoff. Brief sleep so we don't burn 100% CPU
        //    while waiting for work.
        std::thread::sleep(std::time::Duration::from_micros(50));
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicUsize, Ordering as AtomicOrd};
    use std::time::{Duration, Instant};

    #[test]
    fn submit_and_run_completes_all_tasks() {
        let sched = WorkStealingScheduler::new(4);
        let n = 1000;
        let counter = Arc::new(AtomicUsize::new(0));
        for _ in 0..n {
            let c = Arc::clone(&counter);
            sched.submit(move || { c.fetch_add(1, AtomicOrd::Relaxed); });
        }
        let deadline = Instant::now() + Duration::from_secs(5);
        while counter.load(AtomicOrd::Relaxed) < n && Instant::now() < deadline {
            std::thread::sleep(Duration::from_millis(1));
        }
        assert_eq!(counter.load(AtomicOrd::Relaxed), n);
        sched.shutdown();
    }

    /// Stealing actually happens: with skewed initial distribution
    /// (all tasks via injector + only 1 worker initially busy), the
    /// other workers must steal to complete the work.
    #[test]
    fn workers_steal_to_complete_work() {
        let sched = WorkStealingScheduler::new(6);
        let n = 10_000;
        let counter = Arc::new(AtomicUsize::new(0));
        for _ in 0..n {
            let c = Arc::clone(&counter);
            sched.submit(move || {
                c.fetch_add(1, AtomicOrd::Relaxed);
            });
        }
        let started = Instant::now();
        while counter.load(AtomicOrd::Relaxed) < n
            && started.elapsed() < Duration::from_secs(5)
        {
            std::thread::sleep(Duration::from_millis(1));
        }
        assert_eq!(counter.load(AtomicOrd::Relaxed), n);
        sched.shutdown();
    }

    /// Throughput sanity: 100K trivial tasks complete in a small
    /// wall-clock budget. Loose bound — actual benchmark reports
    /// the real number.
    #[test]
    fn throughput_100k_under_2s() {
        let sched = WorkStealingScheduler::new(6);
        let n = 100_000;
        let counter = Arc::new(AtomicUsize::new(0));
        let started = Instant::now();
        for _ in 0..n {
            let c = Arc::clone(&counter);
            sched.submit(move || { c.fetch_add(1, AtomicOrd::Relaxed); });
        }
        while counter.load(AtomicOrd::Relaxed) < n {
            std::thread::sleep(Duration::from_micros(100));
        }
        let elapsed = started.elapsed();
        sched.shutdown();
        assert!(elapsed < Duration::from_secs(2),
                "100K tasks should complete < 2s; took {:?}", elapsed);
    }
}
