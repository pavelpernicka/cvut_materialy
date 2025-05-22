#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define RETURN_ERR_INPUT 100
#define RETURN_ERR_LENGTH 101
#define INITIAL_BUFFER_SIZE 15
#define ALPHABET_SIZE 52
#define MIN(a, b) ((a) < (b) ? (a) : (b))

char rotate(char, int);
void shift(const char *, char *, int);
char *read_line();
char *best_shift_match(const char *, const char *, int);
int levenshtein_distance(const char *a, const char *b);

int main() {
    char *encoded = read_line();
    char *partial_decoded = read_line();

    if (!encoded || !partial_decoded) {
        fprintf(stderr, "Error: Chybny vstup!\n");
        free(encoded); encoded = NULL;
        free(partial_decoded); partial_decoded = NULL;
        return RETURN_ERR_INPUT;
    }

    int enc_len = strlen(encoded);

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

char *read_line() {
  // at begining allocate space for 15 chars
  int size = sizeof(char) * INITIAL_BUFFER_SIZE;
  char *new_string = malloc(size);
  if (!new_string) {
    return NULL;
  }

  int len = 0;
  int curr_char;

  // read input until it newline
  while ((curr_char = getchar()) != '\n') {
    // out of alphabet range
    if (!isalpha(curr_char)) {
      free(new_string);
      return NULL;
    }

    // reallocate double of space if last size + "\0" is used
    if (len + 1 >= size) {
      size *= 2;
      char *tmp = realloc(new_string, size);
      if (!tmp) {
        free(new_string);
        return NULL;
      }
      new_string = tmp;
    }
    new_string[len] = curr_char;
    len++;
  }

  new_string[len] = '\0';
  return new_string;
}

char *best_shift_match(const char *encoded, const char *partial, int len) {
    int best_distance = -1;
    int best_shift = 0;

    char *candidate = malloc(len + 1);
    if (!candidate) return NULL;

    for (int i = 0; i < ALPHABET_SIZE; i++) {
        shift(encoded, candidate, i);
        int distance = levenshtein_distance(candidate, partial);
        if (best_distance == -1 || distance < best_distance) {
            best_distance = distance;
            best_shift = i;
        }
    }

    shift(encoded, candidate, best_shift);
    return candidate;
}

int levenshtein_distance(const char *a, const char *b) {
    int len_a = strlen(a);
    int len_b = strlen(b);

    int **dp = malloc((len_a + 1) * sizeof(int *));
    for (int i = 0; i <= len_a; i++) {
        dp[i] = malloc((len_b + 1) * sizeof(int));
    }

    for (int i = 0; i <= len_a; i++) dp[i][0] = i;
    for (int j = 0; j <= len_b; j++) dp[0][j] = j;

    for (int i = 1; i <= len_a; i++) {
        for (int j = 1; j <= len_b; j++) {
            int cost = (a[i - 1] == b[j - 1]) ? 0 : 1;
            dp[i][j] = MIN(
                MIN(dp[i - 1][j] + 1,     // delete
                    dp[i][j - 1] + 1),    // insert
                dp[i - 1][j - 1] + cost   // substition
            );
        }
    }

    int result = dp[len_a][len_b];
    for (int i = 0; i <= len_a; i++) free(dp[i]);
    free(dp);

    return result;
}

