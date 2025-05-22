#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <ctype.h>

#define MAX_MATRICES 26

typedef struct {
    int rows, cols;
    int *data;
} Matrix;

enum exitcode {
    ALLOCATION_ERROR = 1,
    INPUT_ERROR = 100
};

Matrix parse_matrix_definition(const char *line);
Matrix add(const Matrix *a, const Matrix *b, int sign);
Matrix multiply(const Matrix *a, const Matrix *b);
void free_matrix(Matrix *m);
void print_matrix(const Matrix *m);

char *read_line(void) {
    int capacity = 128;
    int length = 0;
    char *buffer = malloc(capacity);
    if (!buffer) exit(ALLOCATION_ERROR);

    int c;
    while ((c = getchar()) != EOF && c != '\n') {
        if (length + 1 >= capacity) {
            capacity *= 2;
            char *new_buffer = realloc(buffer, capacity);
            if (!new_buffer) {
                free(buffer);
                exit(ALLOCATION_ERROR);
            }
            buffer = new_buffer;
        }
        buffer[length++] = c;
    }

    if (c == EOF && length == 0) {
        free(buffer);
        return NULL;
    }

    buffer[length] = '\0';
    return buffer;
}

int main() {
    Matrix matrices[MAX_MATRICES] = {0};
    bool defined[MAX_MATRICES] = {0};

    char *line;
    while ((line = read_line()) != NULL) {
        if (line[0] == '\0') {
            free(line);
            break;
        }

        if (!strchr(line, '=')) {
            fprintf(stderr, "Error: Chybny vstup!\n");
            free(line);
            return INPUT_ERROR;
        }

        char name = line[0];
        if (!isupper(name)) {
            fprintf(stderr, "Error: Chybny vstup!\n");
            free(line);
            return INPUT_ERROR;
        }

        if (defined[name - 'A']) {
            free_matrix(&matrices[name - 'A']);
        }

        matrices[name - 'A'] = parse_matrix_definition(line);
        defined[name - 'A'] = true;
        free(line);
    }

    line = read_line();
    if (!line) {
        fprintf(stderr, "Error: Chybny vstup!\n");
        return INPUT_ERROR;
    }

    Matrix *stack[MAX_MATRICES];
    int stack_top = -1;
    char op_stack[MAX_MATRICES];
    int op_top = -1;

    for (char *p = line; *p;) {
        if (isspace(*p)) {
            p++;
            continue;
        }

        if (isupper(*p)) {
            if (!defined[*p - 'A']) {
                fprintf(stderr, "Error: Chybny vstup!\n");
                free(line);
                return INPUT_ERROR;
            }
            Matrix *m = malloc(sizeof(Matrix));
            if (!m) exit(ALLOCATION_ERROR);
            *m = matrices[*p - 'A'];
            m->data = malloc(sizeof(int) * m->rows * m->cols);
            if (!m->data) exit(ALLOCATION_ERROR);
            memcpy(m->data, matrices[*p - 'A'].data, sizeof(int) * m->rows * m->cols);
            stack[++stack_top] = m;
            p++;
        } else if (*p == '+' || *p == '-' || *p == '*') {
            char op = *p;
            int op_pri = (op == '*') ? 2 : 1;

            while (op_top >= 0) {
                char prev_op = op_stack[op_top];
                int prev_pri = (prev_op == '*') ? 2 : 1;

                if (prev_pri >= op_pri) {
                    Matrix *b = stack[stack_top--];
                    Matrix *a = stack[stack_top--];
                    char op2 = op_stack[op_top--];

                    Matrix res = (op2 == '*') ? multiply(a, b) : add(a, b, op2 == '+' ? 1 : -1);

                    free_matrix(a);
                    free_matrix(b);
                    free(a);
                    free(b);

                    Matrix *res_ptr = malloc(sizeof(Matrix));
                    if (!res_ptr) exit(ALLOCATION_ERROR);
                    *res_ptr = res;
                    stack[++stack_top] = res_ptr;
                } else {
                    break;
                }
            }

            op_stack[++op_top] = op;
            p++;
        } else {
            fprintf(stderr, "Error: Chybny vstup!\n");
            free(line);
            return INPUT_ERROR;
        }
    }

    while (op_top >= 0) {
        Matrix *b = stack[stack_top--];
        Matrix *a = stack[stack_top--];
        char op = op_stack[op_top--];

        Matrix res = (op == '*') ? multiply(a, b) : add(a, b, op == '+' ? 1 : -1);

        free_matrix(a);
        free_matrix(b);
        free(a);
        free(b);

        Matrix *res_ptr = malloc(sizeof(Matrix));
        if (!res_ptr) exit(ALLOCATION_ERROR);
        *res_ptr = res;
        stack[++stack_top] = res_ptr;
    }

    print_matrix(stack[0]);
    free_matrix(stack[0]);
    free(stack[0]);
    free(line);
    return 0;
}

Matrix parse_matrix_definition(const char *line) {
    const char *p = strchr(line, '[');
    if (!p) {
        fprintf(stderr, "Error: Chybny vstup!\n");
        exit(INPUT_ERROR);
    }
    p++;

    int rows = 1, cols = 0, tmp_cols = 0, capacity = 16;
    int *data = malloc(sizeof(int) * capacity);
    if (!data) exit(ALLOCATION_ERROR);

    while (*p && *p != ']') {
        if (*p == ';') {
            if (cols == 0)
                cols = tmp_cols;
            else if (tmp_cols != cols) {
                fprintf(stderr, "Error: Chybny vstup!\n");
                free(data);
                exit(INPUT_ERROR);
            }
            tmp_cols = 0;
            rows++;
            p++;
            continue;
        }

        if (isspace(*p)) {
            p++;
            continue;
        }

        char *end;
        int val = strtol(p, &end, 10);
        if (p == end) {
            fprintf(stderr, "Error: Chybny vstup!\n");
            free(data);
            exit(INPUT_ERROR);
        }

        if ((rows - 1) * cols + tmp_cols >= capacity) {
            capacity *= 2;
            int *new_data = realloc(data, sizeof(int) * capacity);
            if (!new_data) {
                free(data);
                exit(ALLOCATION_ERROR);
            }
            data = new_data;
        }

        data[(rows - 1) * cols + tmp_cols++] = val;
        p = end;
    }

    if (cols == 0)
        cols = tmp_cols;
    else if (tmp_cols != cols) {
        fprintf(stderr, "Error: Chybny vstup!\n");
        free(data);
        exit(INPUT_ERROR);
    }

    Matrix m;
    m.rows = rows;
    m.cols = cols;
    m.data = malloc(sizeof(int) * rows * cols);
    if (!m.data) {
        free(data);
        exit(ALLOCATION_ERROR);
    }

    for (int i = 0; i < rows * cols; i++)
        m.data[i] = data[i];
    free(data);

    return m;
}

Matrix add(const Matrix *a, const Matrix *b, int sign) {
    if (a->rows != b->rows || a->cols != b->cols) {
        fprintf(stderr, "Error: Chybny vstup!\n");
        exit(INPUT_ERROR);
    }
    Matrix r;
    r.rows = a->rows;
    r.cols = a->cols;
    r.data = malloc(sizeof(int) * r.rows * r.cols);
    if (!r.data) exit(ALLOCATION_ERROR);

    for (int i = 0; i < r.rows * r.cols; i++)
        r.data[i] = a->data[i] + sign * b->data[i];

    return r;
}

Matrix multiply(const Matrix *a, const Matrix *b) {
    if (a->cols != b->rows) {
        fprintf(stderr, "Error: Chybny vstup!\n");
        exit(INPUT_ERROR);
    }
    Matrix r;
    r.rows = a->rows;
    r.cols = b->cols;
    r.data = malloc(sizeof(int) * r.rows * r.cols);
    if (!r.data) exit(ALLOCATION_ERROR);

    for (int i = 0; i < r.rows; i++)
        for (int j = 0; j < r.cols; j++) {
            r.data[i * r.cols + j] = 0;
            for (int k = 0; k < a->cols; k++)
                r.data[i * r.cols + j] += a->data[i * a->cols + k] * b->data[k * b->cols + j];
        }

    return r;
}

void print_matrix(const Matrix *m) {
    putchar('[');
    for (int i = 0; i < m->rows; i++) {
        if (i > 0) printf("; ");
        for (int j = 0; j < m->cols; j++) {
            if (j > 0) putchar(' ');
            printf("%d", m->data[i * m->cols + j]);
        }
    }
    puts("]");
}

void free_matrix(Matrix *m) {
    free(m->data);
    m->data = NULL;
}
