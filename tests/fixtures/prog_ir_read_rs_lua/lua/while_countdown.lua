function while_countdown(n)
  local m = n
  local steps = 0
  while m > 0 do
    m = m - 1
    steps = steps + 1
  end
  return steps
end
