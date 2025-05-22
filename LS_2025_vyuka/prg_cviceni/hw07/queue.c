#include <stdlib.h>
#include <stdbool.h>
#include "queue.h"

typedef struct Node{
    void *data;
    struct Node *next;
} Node;

typedef struct Queue{
    Node *head;
    Node *tail;
    int count;
    int (*compare)(const void *, const void *);
    void (*clear)(void *);
} Queue;

void* create(){
    Queue *q = malloc(sizeof(Queue));
    if (!q) return NULL;
    q->head = NULL;
    q->tail = NULL;
    q->count = 0;
    q->compare = NULL;
    q->clear = NULL;
    return q;
}

void clear(void *queue){
    Queue *q = queue;
    Node *cur = q->head;
    while(cur){
        Node *tmp = cur;
        cur = cur->next;
        if(q->clear){
            q->clear(tmp->data);
        }else{
            free(tmp->data);
        }
        free(tmp);
    }
    q->head = q->tail = NULL;
    q->count = 0;
}

void setClear(void *queue, void (*clear)(void *)){
    ((Queue*)queue)->clear = clear;
}

void setCompare(void *queue, int (*compare)(const void *, const void *)){
    ((Queue*)queue)->compare = compare;
}

bool push(void *queue, void *entry){
    if (!queue || !entry) return false;
    Queue *q = queue;

    Node *new_node = malloc(sizeof(Node));
    if (!new_node) return false;

    new_node->data = entry;
    new_node->next = NULL;

    if(!q->head){
        q->head = q->tail = new_node;
    }else{
        q->tail->next = new_node;
        q->tail = new_node;
    }

    q->count++;
    return true;
}

void* pop(void *queue){
    if (!queue) return NULL;
    Queue *q = queue;
    if (!q->head) return NULL;

    Node *node = q->head;
    void *data = node->data;
    q->head = node->next;
    if (!q->head) q->tail = NULL;
    free(node);
    q->count--;
    return data;
}

bool insert(void *queue, void *entry){
    if (!queue || !entry) return false;
    Queue *q = queue;
    if (!q->compare) return false;

    Node *new_node = malloc(sizeof(Node));
    if (!new_node) return false;
    new_node->data = entry;
    new_node->next = NULL;

    if(!q->head || q->compare(entry, q->head->data) >= 0){
        new_node->next = q->head;
        q->head = new_node;
        if (!q->tail) q->tail = new_node;
    }else{
        Node *prev = NULL;
        Node *cur = q->head;
        while(cur && q->compare(entry, cur->data) < 0){
            prev = cur;
            cur = cur->next;
        }
        new_node->next = cur;
        prev->next = new_node;
        if (!cur) q->tail = new_node;
    }

    q->count++;
    return true;
}

bool erase(void *queue, void *entry) {
    if (!queue || !entry) return false;
    Queue *q = queue;
    if (!q->compare) return false;

    Node *cur = q->head;
    Node *prev = NULL;
    bool removed = false;

    while(cur){
        if(q->compare(entry, cur->data) == 0){
            Node *to_delete = cur;
            if(prev){
                prev->next = cur->next;
            }else{
                q->head = cur->next;
            }
            if(cur == q->tail) q->tail = prev;
            cur = cur->next;
            if(q->clear){
                q->clear(to_delete->data);
            }else{
                free(to_delete->data);
            }
            free(to_delete);
            q->count--;
            removed = true;
        }else{
            prev = cur;
            cur = cur->next;
        }
    }
    return removed;
}

void* getEntry(const void *queue, int idx){
    const Queue *q = queue;
    if(idx < 0 || idx >= q->count) return NULL;

    Node *cur = q->head;
    for(int i = 0; i < idx; i++){
        cur = cur->next;
    }
    return cur ? cur->data : NULL;
}

int size(const void *queue){
    const Queue *q = queue;
    return q->count;
}

