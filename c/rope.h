#ifndef ROPE_H
#define ROPE H

struct Rope;
typedef struct Rope Rope;

enum Encoding {
  ASCII,
  UTF_8,
  UTF_16,
  UTF_32
};

typedef enum Encoding Encoding;

Rope* Rope_rereference(Rope*);
void Rope_destruct(Rope*);

void Rope_write(Rope*, Encoding, FILE);
Rope* Rope_read(Encoding, FILE);

Rope* Rope_concatenate(Rope* r0, Rope* r1);

size_t Rope_length(Rope*) __attribute__((pure));

#endif
