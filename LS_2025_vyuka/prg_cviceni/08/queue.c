#include <stdio.h>
#include <stdlib.h>

typedef struct node {
    int data;
    struct node *next;
} node_t;

typedef struct {
	node_t *head;
	size_t size;
} queue_t;

int pop(queue_t *q, int *out_value){
	if(q == NULL || q->head == NULL) return 1;
	node_t *tmp = q->head;
	q->head = tmp->next;
	q->size -= 1;
	*out_value = tmp->val;
	free(tmp);
	return 0;
}

int push(queue_t *q, int in_value){
	if(q == NULL) return 1;
	node_t *new_node = malloc(sizeof(node_t));
	new_node->val = in_valuee;
	new_node->next = NULL;
	
	if(q->head == NULL){
		q->head = new_node;
		return 0;
	} else{
		node_t *tmp = q->head;
		while(tmp->next!= NULL){
			tmp = tmp->next;
		}
		tmp->next = new_node;
	}
	q->size += 1;
	return 0;
}

/**
 * Initialize queue.
 * @return: initialized queue
 */
struct QUEUE init_queue();

/**
 * Prints queue q
 * @param q: queue to print
 */
void print_queue(struct QUEUE *q);

/**
 * Pushes element to queue
 * @param q: queue
 * @param username: student username
 * @param hwname: homework name
 * @param points: points awarded for homework
 */
void push_queue(struct QUEUE *q, char *username, char *hwname, double points);

/**
 * Checks if queue q is empty
 * @param q: queue
 * @return: 1 if empty, 0 otherwise
 */
int is_empty(struct QUEUE *q);

/**
 * Pops element from queue.
 * @param q: queue
 * @return: element from queue.
 */
struct homework pop_queue(struct QUEUE *q);

/**
 * Frees queue.
 * @param q: queue
 */
void free_queue(struct QUEUE *q);


int main(int argc, char const *argv[])
{
    // TODO implement queue
    return 0;
}
