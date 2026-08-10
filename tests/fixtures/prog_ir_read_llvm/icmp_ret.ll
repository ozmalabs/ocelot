; ret of a bare icmp result — i1 stays an in-frame integer 0/1
define i1 @isneg(i32 %x) {
  %c = icmp slt i32 %x, 0
  ret i1 %c
}
