#include "queue.h"

bool resize_queue(queue_t *queue, int new_capacity) {
  if (new_capacity < queue->size) {
    return false;
  }

  void **new_data = (void **)malloc(sizeof(void *) * new_capacity);
  if (!new_data) {
    return false;
  }

  // copy data
  for (int i = 0; i < queue->size; ++i) {
    int idx = (queue->head + i) % queue->capacity;
    new_data[i] = queue->data[idx];
  }

  free(queue->data);
  queue->data = new_data;
  queue->capacity = new_capacity;
  queue->head = 0;
  queue->tail = queue->size;

  return true;
}

queue_t *create_queue(int capacity) {
  if (capacity <= 0) {
    return NULL;
  }

  queue_t *queue = (queue_t *)malloc(sizeof(queue_t));
  if (!queue) {
    return NULL;
  }

  queue->data = (void **)malloc(sizeof(void *) * capacity);
  if (!queue->data) {
    free(queue);
    return NULL;
  }

  queue->capacity = capacity;
  queue->size = 0;
  queue->head = 0;
  queue->tail = 0;

  return queue;
}

void delete_queue(queue_t *queue) {
  if (!queue) {
    return;  // cant return signaling
  }
  free(queue->data);
  queue->data = NULL;
  free(queue);
}

bool push_to_queue(queue_t *queue, void *data) {
  if (!queue) {
    return false;
  }

  // upsizing
  if (queue->size == queue->capacity) {
    if (!resize_queue(queue, queue->capacity * 2)) {
      return false;
    }
  }

  queue->data[queue->tail] = data;
  queue->tail = (queue->tail + 1) % queue->capacity;
  queue->size++;
  return true;
}

void *pop_from_queue(queue_t *queue) {
  if (!queue || queue->size == 0) {
    return NULL;
  }

  void *previous_data = queue->data[queue->head];
  queue->head = (queue->head + 1) % queue->capacity;
  queue->size--;

  // downsizing (<1/3 => half)
  if (queue->capacity > 1 && queue->size <= queue->capacity / 3) {
    int new_capacity = queue->capacity / 2;
    resize_queue(queue, new_capacity);  // TODO - handling
  }

  return previous_data;
}

void *get_from_queue(queue_t *queue, int idx) {
  if (!queue || idx < 0 || idx >= queue->size) {
    return NULL;
  }

  int pos = queue->head + idx;
  return queue->data[pos];
}

int get_queue_size(queue_t *queue) {
  if (!queue) {
    return 0;
  }
  return queue->size;
}

