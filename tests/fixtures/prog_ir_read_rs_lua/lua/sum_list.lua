function sum_list(xs)
  local total = 0
  for k, v in ipairs(xs) do
    total = total + v
  end
  return total
end
