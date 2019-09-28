struct StackNode;
typedef struct StackNode StackNode;
struct StackNode {
  Object value;
  StackNode* next;
};

struct Stack;
typedef struct Stack Stack;
struct Stack {
  StackNode* top;
};

void Stack_initialize(Stack* self) {
  self->top = NULL;
}

bool Stack_isEmpty(Stack* self) {
  return self->top == NULL;
}

Object Stack_pop(Stack*);

void Stack_deinitialize(Stack* self) {
  while(self->top != NULL) {
    Object o = Stack_pop(self);
    Object_deinitialize(&o);
  }
}

void Stack_push(Stack* self, Object value) {
  StackNode* node = malloc(sizeof(StackNode));
  node->value = value;
  node->next = self->top;
  self->top = node;
}

Object Stack_pop(Stack* self) {
  assert(self->top != NULL);

  StackNode* node = self->top;
  self->top = node->next;

  Object result = node->value;
  free(node);
  return result;
}
