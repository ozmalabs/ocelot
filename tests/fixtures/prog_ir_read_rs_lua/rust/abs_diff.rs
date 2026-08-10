fn abs_diff(a: i64, b: i64) -> i64 {
    let d = a - b;
    if d < 0 { -d } else { d }
}
