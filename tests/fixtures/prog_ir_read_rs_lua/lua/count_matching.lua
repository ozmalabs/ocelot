function count_matching(xs, t)
  local c = 0
  for i = 1, #xs do
    if xs[i] == t then
      c = c + 1
    end
  end
  return c
end
