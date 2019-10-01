void inst_{{ name }}(struct Thread* thread, const union Argument argument) {
  // We're going to reuse result as both the first input and the result
  assert(!Stack_isEmpty(&(thread->stack)));
  Object result = Stack_pop(&(thread->stack));
  assert(result.type == INTEGER);

  assert(!Stack_isEmpty(&(thread->stack)));
  Object other = Stack_pop(&(thread->stack));
  assert(other.type == INTEGER);

  result.value.integer = other.value.integer {{ operation }} result.value.integer;

  Stack_push(&(thread->stack), result);
}
