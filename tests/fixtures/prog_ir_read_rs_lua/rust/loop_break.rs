fn loop_break(n: i64) -> i64 {
    let mut i = 0;
    loop {
        if i == n {
            break;
        }
        i += 1;
    }
    i
}
