; icmp + select chain (clamp x into [0, 100])
define i32 @clamp(i32 %x) {
  %neg = icmp slt i32 %x, 0
  %z = select i1 %neg, i32 0, i32 %x
  %big = icmp sgt i32 %z, 100
  %r = select i1 %big, i32 100, i32 %z
  ret i32 %r
}
