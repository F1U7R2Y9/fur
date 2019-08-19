#ifndef QUEUE_H
#define QUEUE_H

struct Queue;
typedef struct Queue Queue;

Queue* Queue_construct();

void Queue_enqueue(Queue*, void*);
void* Queue_dequeue(Queue*, void* defaultValue);

#endif
