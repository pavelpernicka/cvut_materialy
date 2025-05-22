#include <stdlib.h>
#include <stdbool.h>
#include "linked_list.h"

typedef struct Node{
    int value;
    struct Node *next;
} Node;

static Node *head = NULL;
static Node *tail = NULL;
static int count = 0;

bool push(int entry){
    if (entry < 0) return false;

    Node *new_node = malloc(sizeof(Node));
    if (!new_node) return false;

    new_node->value = entry;
    new_node->next = NULL;

    if (!head){ // empty list
        head = tail = new_node;
    }else{
        tail->next = new_node;
        tail = new_node;
    }

    count++;
    return true;
}

int pop(void) {
    if(!head) return -1;

    Node *node = head;
    int value = node->value;
    head = head->next;
    if(!head){
        tail = NULL;
    }
    free(node);
    count--;
    return value;
}

bool insert(int entry){
    if (entry < 0) return 0;

    Node *new_node = malloc(sizeof(Node));
    if (!new_node) return 0;
    new_node->value = entry;
    new_node->next = NULL;

    if(!head || entry > head->value){
        new_node->next = head;
        head = new_node;
        if (!tail) tail = new_node; // empty list -> set tail
    }else{
        // find first node with value <= entry
        Node *prev = NULL;
        Node *cur = head;

        while(cur && entry < cur->value){
            prev = cur;
            cur = cur->next;
        }

        // insert new node between prev and cur
        new_node->next = cur;
        if (prev) {
            prev->next = new_node;
        } else {
            head = new_node;    
        }
        if (cur == NULL) {
            tail = new_node;
        }
    }

    count++;
    return 1;
}

bool erase(int entry){
    if (!head) return false;

    bool removed = false;
    Node *cur = head;
    Node *prev = NULL;

    while(cur){
        if(cur->value == entry){
            Node *to_delete = cur;
            if(prev){
                // skip current node
                prev->next = cur->next;
            }else{
                head = cur->next;
            }
            if(cur == tail){
                tail = prev;
            }
            cur = cur->next;
            free(to_delete);
            count--;
            removed = true;
        }else{
            prev = cur;
            cur = cur->next;
        }
    }
    return removed;
}

int getEntry(int idx){
    if (idx < 0 || idx >= count) return -1;

    Node *cur = head;
    for (int i = 0; i < idx; i++){
        cur = cur->next;
    }

    return cur ? cur->value : -1;
}

int size(void){
    return count;
}

void clear(void){
    Node *cur = head;
    while (cur){
        Node *tmp = cur;
        cur = cur->next;
        free(tmp);
    }

    head = tail = NULL;
    count = 0;
}

