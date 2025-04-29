#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int key;
    char *value;
} pair;  // structure

void read_from_stdin_write_file(const char *filename);

void read_from_file_write_stdout(const char *filename);

void fill_struct(pair *pair_struct);

void write_struct_to_file(const pair *pair_struct, const char *filename);


int main()
{
    /* TODO */
    return 0;
}
