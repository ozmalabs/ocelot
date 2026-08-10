//! Polynomial evaluator — naive baseline.
//!
//! Computes p(x) = 3x^4 - 2x^3 + x - 5 by calling pow() for each term.
//! Deliberately written as the slow textbook form so the cortex has
//! something measurable to beat with Horner's method.

#[no_mangle]
pub extern "C" fn eval_poly(x: i64) -> i64 {
    // 3*x^4 - 2*x^3 + 0*x^2 + 1*x - 5
    let t4 = 3i64.wrapping_mul(x.wrapping_pow(4));
    let t3 = (-2i64).wrapping_mul(x.wrapping_pow(3));
    let t1 = x;
    let t0: i64 = -5;
    t4.wrapping_add(t3).wrapping_add(t1).wrapping_add(t0)
}
