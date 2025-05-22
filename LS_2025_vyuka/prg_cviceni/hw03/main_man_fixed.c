#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define RETURN_ERR_INPUT 100
#define RETURN_ERR_LENGTH 101
#define INITIAL_BUFFER_SIZE 15
#define ALPHABET_SIZE 52

char rotate(char, int);
void shift(const char *, char *, int);
int compare(const char *, const char *);
char *read_line();
char *best_shift_match(const char *, const char *, int);

int main() {
    char *encoded = read_line();
    char *partial_decoded = read_line();

    if (!encoded || !partial_decoded) {
        fprintf(stderr, "Error: Chybny vstup!\n");
        free(encoded); encoded = NULL;
        free(partial_decoded); partial_decoded = NULL;
        return RETURN_ERR_INPUT;
    }

    int enc_len = strlen(encoded); // použijeme strlen()
    if (enc_len != (int)strlen(partial_decoded)) {
        fprintf(stderr, "Error: Chybna delka vstupu!\n");
        free(encoded); encoded = NULL;
        free(partial_decoded); partial_decoded = NULL;
        return RETURN_ERR_LENGTH;
    }

    char *result = best_shift_match(encoded, partial_decoded, enc_len);
    printf("%s\n", result);

    free(encoded);
    free(partial_decoded);
    free(result);
    return 0;
}

char rotate(char original, int offset) {
    int pos;

    if (islower(original)) {
        pos = (offset + (original - 'a')) % ALPHABET_SIZE;
    } else if (isupper(original)) {
        pos = (offset + (original - 'A') + 26) % ALPHABET_SIZE;
    } else {
        return original;
    }

    if (pos < 26) return 'a' + pos;
    else return 'A' + (pos - 26);
}

void shift(const char *src, char *dst, int offset) {
    int i = 0;
    while (src[i] != '\0') {
        dst[i] = rotate(src[i], offset);
        i++;
    }
    dst[i] = '\0';
}

int compare(const char *str1, const char *str2) {
    int i = 0, score = 0;
    while (str1[i] != '\0' && str2[i] != '\0') {
        if (str1[i] == str2[i]) score++;
        i++;
    }
    return score;
}

char *read_line() {
    int size = INITIAL_BUFFER_SIZE;
    char *new_string = malloc(size);
    if (!new_string) return NULL;

    int len = 0;
    int curr_char;

    while ((curr_char = getchar()) != '\n' && curr_char != EOF) {
        if (!isalpha(curr_char)) {
            free(new_string);
            new_string = NULL;
            return NULL;
        }

        if (len + 1 >= size) {
            size *= 2;
            char *tmp = realloc(new_string, size);
            if (!tmp) {
                free(new_string);
                return NULL;
            }
            new_string = tmp;
        }

        new_string[len++] = (char)curr_char;
    }

    new_string[len] = '\0';
    return new_string;
}

char *best_shift_match(const char *encoded, const char *partial, int len) {
    char *best = malloc(len + 1);
    if (!best) return NULL;

    char *temp = malloc(len + 1);
    if (!temp) {
        free(best);
        return NULL;
    }

    int best_score = -1;
    int best_shift = 0;

    for (int i = 0; i < ALPHABET_SIZE; i++) {
        shift(encoded, temp, i);
        int score = compare(temp, partial);
        if (score > best_score) {
            best_score = score;
            best_shift = i;
        }
    }

    shift(encoded, best, best_shift);
    free(temp);
    return best;
}

