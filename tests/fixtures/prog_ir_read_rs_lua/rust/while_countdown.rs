fn while_countdown(n: i64) -> i64 {
    let mut m = n;
    let mut steps = 0;
    while m > 0 {
        m = m - 1;
        steps += 1;
    }
    steps
}
