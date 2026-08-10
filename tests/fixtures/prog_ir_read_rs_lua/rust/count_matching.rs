fn count_matching(xs: Vec<i64>, t: i64) -> i64 {
    let mut c = 0;
    for x in xs {
        if x == t {
            c += 1;
        }
    }
    c
}
