#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX 1000000    // 10^6
#define NUM_PRIMES 79000 // expected number of primes < MAX
#define ERR_INPUT 100
#define MAX_DIGITS 101

typedef struct {
    int digits[MAX_DIGITS]; // reverse order
    int len;
} BigInt;

typedef struct {
    int *primes;
    int count;
} PrimeList;

void prepare_primes(PrimeList *plist);
void decompose_bigint(const char *str, const PrimeList *plist);
BigInt parse_bigint(const char *str);
bool is_one(const BigInt *n);
bool divisible_by(const BigInt *n, int p);
void divide_by(BigInt *n, int p);

int main(void) {
    PrimeList plist;
    plist.primes = malloc(sizeof(int) * NUM_PRIMES);
    if (!plist.primes) {
        fprintf(stderr, "Error: Allocation failed\n");
        return 1;
    }

    prepare_primes(&plist);

    char input[MAX_DIGITS];
    while (1) {
        if (!fgets(input, sizeof(input), stdin)) {
            fprintf(stderr, "Error: Chybny vstup!\n");
            free(plist.primes);
            return ERR_INPUT;
        }

        size_t len = strlen(input);
        if (input[len - 1] == '\n') input[len - 1] = '\0';

        if (strcmp(input, "0") == 0) break;

        for (size_t i = 0; i < strlen(input); ++i) {
            if (input[i] < '0' || input[i] > '9') {
                fprintf(stderr, "Error: Chybny vstup!\n");
                free(plist.primes);
                return ERR_INPUT;
            }
        }

        decompose_bigint(input, &plist);
    }

    free(plist.primes);
    return 0;
}

void prepare_primes(PrimeList *plist) {
    /*
      Prepares array of prime numbers up to MAX using Eratosthenes sieve method
    */
    bool excluded[MAX] = {false};
    plist->count = 0;
    for (int i = 2; i < MAX; ++i) {
        if (!excluded[i]) {
            plist->primes[plist->count++] = i;
            for (int j = i * 2; j < MAX; j += i) {
                excluded[j] = true;
            }
        }
    }
}

void decompose_bigint(const char *str, const PrimeList *plist) {
    BigInt n = parse_bigint(str);
    printf("Prvociselny rozklad cisla %s je:\n", str);

    if (is_one(&n)) {
        printf("1\n");
        return;
    }

    int first = 1;
    for (int i = 0; i < plist->count; ++i) {
        int factor = 0;
        while (divisible_by(&n, plist->primes[i])) {
            divide_by(&n, plist->primes[i]);
            factor++;
        }
        if (factor > 0) {
            if (!first) printf(" x ");
            first = 0;
            if (factor == 1)
                printf("%d", plist->primes[i]);
            else
                printf("%d^%d", plist->primes[i], factor);
        }
    }

    if (!is_one(&n)) {
        if (!first) printf(" x ");
        for (int i = n.len - 1; i >= 0; --i) printf("%d", n.digits[i]);
    }
    printf("\n");
}

BigInt parse_bigint(const char *str) {
    BigInt result = {{0}, 0};
    result.len = strlen(str);
    for (int i = 0; i < result.len; ++i)
        result.digits[i] = str[result.len - i - 1] - '0';
    return result;
}

bool is_one(const BigInt *n) {
    return n->len == 1 && n->digits[0] == 1;
}

bool divisible_by(const BigInt *n, int p) {
    BigInt tmp = *n;
    divide_by(&tmp, p);
    BigInt test = *n;
    int rem = 0;
    for (int i = test.len - 1; i >= 0; --i)
        rem = (rem * 10 + test.digits[i]) % p;
    return rem == 0;
}

void divide_by(BigInt *n, int p) {
    int rem = 0;
    for (int i = n->len - 1; i >= 0; --i) {
        int current = rem * 10 + n->digits[i];
        n->digits[i] = current / p;
        rem = current % p;
    }

    while (n->len > 1 && n->digits[n->len - 1] == 0) {
        n->len--;
    }
}

