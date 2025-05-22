#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

typedef struct {
    // 1D array, indexes will be calculated
    int rows, cols;
    int *data;
} Matrix;

enum exitcode {
	ALLOCATION_ERROR = 1,
	INPUT_ERROR = 100
};

Matrix read_matrix();
void print_matrix(const Matrix *m);
Matrix add(const Matrix *a, const Matrix *b, int sign);
Matrix multiply(const Matrix *a, const Matrix *b);
void free_matrix(Matrix *m);

int main() {
    int matrix_capacity = 4;
    int matrix_count = 0;
    int operator_capacity = 4;
    int operator_count = 0;

    Matrix *mats = malloc(sizeof(Matrix) * matrix_capacity);
    char *ops = malloc(sizeof(char) * operator_capacity);
    if (!mats || !ops) return ALLOCATION_ERROR;

    while (1) {
        // mats reallocation
        if (matrix_count >= matrix_capacity) {
            matrix_capacity *= 2;
            mats = realloc(mats, sizeof(Matrix) * matrix_capacity);
            if (!mats) exit(ALLOCATION_ERROR);
        }

        mats[matrix_count++] = read_matrix();

        // read operator
        int c;
        do {
            c = getchar();
        } while (c == '\n' || c == ' ');

        if (c == EOF) break;

        if (c != '+' && c != '-' && c != '*') {
            fprintf(stderr, "Error: Chybny vstup!\n");
            for (int i = 0; i < matrix_count; i++) free_matrix(&mats[i]);
            free(mats);
            free(ops);
            return INPUT_ERROR;
        }

        // rellocate ops
        if (operator_count >= operator_capacity) {
            operator_capacity *= 2;
            ops = realloc(ops, sizeof(char) * operator_capacity);
            if (!ops) exit(ALLOCATION_ERROR);
        }

        ops[operator_count++] = (char)c;
    }

    // do multiplication first, then the others
    int i = 0;
    while (operator_count > 0) {
        // look for '*'
        bool found_mul = false;
        for (int j = 0; j < operator_count; j++) {
            if (ops[j] == '*') {
                i = j;
                found_mul = true;
                break;
            }
        }

        if (!found_mul) i = 0; // no mul, do +- first

        Matrix result;
        if (ops[i] == '*') {
            result = multiply(&mats[i], &mats[i + 1]);
        } else {
            int sign = (ops[i] == '+') ? 1 : -1;
            result = add(&mats[i], &mats[i + 1], sign);
        }

        free_matrix(&mats[i]);
        free_matrix(&mats[i + 1]);
        mats[i] = result;

        // move left
        for (int j = i + 1; j < matrix_count - 1; j++)
            mats[j] = mats[j + 1];
        for (int j = i; j < operator_count - 1; j++)
            ops[j] = ops[j + 1];

        matrix_count--;
        operator_count--;
    }

    print_matrix(&mats[0]);
    free_matrix(&mats[0]);
    free(mats);
    free(ops);
    return 0;
}

Matrix read_matrix() {
	/*
	Create new matrix from stdin
	*/
	
    Matrix m;
    if (scanf("%d %d", &m.rows, &m.cols) != 2 || m.rows <= 0 || m.cols <= 0) {
        fprintf(stderr, "Error: Chybny vstup!\n");
        exit(INPUT_ERROR);
    }

    m.data = malloc(m.rows * m.cols * sizeof(int));
    if (!m.data) exit(ALLOCATION_ERROR);

    for (int i = 0; i < m.rows * m.cols; i++) {
        if (scanf("%d", &m.data[i]) != 1) {
            free(m.data);
            fprintf(stderr, "Error: Chybny vstup!\n");
            exit(INPUT_ERROR);
        }
    }

    return m;
}

void print_matrix(const Matrix *m) {
	/*
	Print matrix to stdout
	*/
	
    printf("%d %d\n", m->rows, m->cols);
    for (int i = 0; i < m->rows; i++) {
        for (int j = 0; j < m->cols; j++) {
            if (j > 0) putchar(' ');
            printf("%d", m->data[i * m->cols + j]);
        }
        putchar('\n');
    }
}

Matrix add(const Matrix *a, const Matrix *b, int sign) {
	/*
	Add or subtract two matrices (specified by sign)
	*/
	
	// must have same shape
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
	/*
	Multiply two matrices
	*/
	
    // rows must equal columns
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

void free_matrix(Matrix *m) {
	/*
	Free matrix content
	*/
	
    free(m->data);
    m->data = NULL;
}

