/*
This is an adaptation of Michael and Scott's lock-free queue.

Whitepaper containing pseudocode can be found here:
https://www.liblfds.org/downloads/white%20papers/[Queue]%20-%20[Michael,%20Scott]%20-%20Simple,%20Fast,%20and%20Practical%20Non-Blocking%20and%20Blocking%20Concurrent%20Queue%20Algorithms.pdf
*/
#ifndef QUEUE_C
#define QUEUE_C

#include<stdbool.h>
#include<stdint.h>
#include<stdlib.h>
#include"queue.h">

struct QueueNodeTaggedPointer;
struct QueueNode;

typedef struct QueueNodeTaggedPointer QueueNodeTaggedPointer;
typedef struct QueueNode QueueNode;

struct QueueNodeTaggedPointer {
  QueueNode* ptr;
  uint64_t count;
};

QueueNodeTaggedPointer QueueNodeTaggedPointer_create(QueueNode* ptr, uint64_t count) {
  QueueNodeTaggedPointer result = { ptr, count };
  return result;
}

struct QueueNode {
  void* value;
  volatile QueueNodeTaggedPointer next;
};

volatile struct Queue {
  QueueNodeTaggedPointer nose;
  QueueNodeTaggedPointer tail;
};

Queue* Queue_construct() {
  QueueNode* dummy = malloc(sizeof(QueueNode));
  dummy->next = NULL;

  Queue* result = malloc(sizeof(Queue));
  result->nose.ptr = dummy;
  result->tail.ptr = dummy;
  return result;
}

void Queue_enqueue(Queue* self, void* value) {
  QueueNode* node = malloc(sizeof(QueueNode));
  node->value = value;
  node->next.ptr = NULL;

  while(true) {
    QueueNodeTaggedPointer tail = self->tail;
    QueueNodeTaggedPointer next = tail.ptr->next;

    if(tail == self->tail) {
      if(next.ptr == NULL) {
        if(__sync_bool_compare_and_swap(&(tail.ptr->next), next, QueueNodeTaggedPointer_create(node, next.count + 1))) {
          __sync_bool_compare_and_swap(&(self->tail), tail, QueueNodeTaggedPointer_create(node, tail.count + 1));
          return;
        }
        else {
          __sync_bool_compare_and_swap(&(self->tail), tail, QueueNodeTaggedPointer_create(next.ptr, tail.count + 1));
        }
      }
    }
  }
}

void* Queue_dequeue(Queue* self, void* defaultValue) {
  while(true) {
    QueueNodeTaggedPointer nose = self->nose;
    QueueNodeTaggedPointer tail = self->tail;
    QueueNodeTaggedPointer head = nose.ptr->next;

    if(nose == self->nose) {
      if(nose.ptr == tail.ptr) {
        if(head.ptr == NULL) {
          return defaultValue;
        }
        else {
          __sync_bool_compare_and_swap(&(self->tail), tail, QueueNodeTaggedPointer_create(head.ptr, tail.count + 1));
        }
      }
      else {
        void* result = head.ptr->value;
        if(__sync_bool_compare_and_swap(&(self->nose), nose, QueueNodeTaggedPointer_create(head.ptr, nose.count + 1))) {
          free(nose.ptr);
          return result;
        }
      }
    }
  }
}

#endif
