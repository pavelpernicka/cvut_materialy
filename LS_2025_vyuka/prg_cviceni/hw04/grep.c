#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#define COLOR_START "\x1b[01;31m\x1b[K"
#define COLOR_END "\x1b[m\x1b[K"

enum exitcode {FOUND, NOT_FOUND, INVALID_ARGUMENT, FILE_READ_ERROR };

int c_strlen(const char* str);
bool c_strcmp(const char* a, const char* b);
bool str_match(const char* text, const char* pattern);
bool str_regmatch(const char* text, const char* pattern);
void colorprint(const char* text, const char* pattern);
char* read_line(FILE* file);

int main(int argc, char* argv[])
{
    const char* pattern = NULL;
    const char* filename = NULL;
    bool use_color = false;
    bool use_regular = false;
    int arg_iterator = 1;

    // handling switches (daplicates and unknown"switches" will be handled as
    // further args)
    while (arg_iterator < argc && argv[arg_iterator][0] == '-') {
        if (c_strcmp(argv[arg_iterator], "--color=always") && !use_color) {
            use_color = true;
        } else if (c_strcmp(argv[arg_iterator], "-E") && !use_regular) {
            use_regular = true;
        } else {
            // fprintf(stderr, "Unknown option: %s\n", argv[arg_iterator]);
            // return 2;
            break; // handle unknown arg as further arg
        }
        arg_iterator++;
    }

    // incorrect number of arguments
    if (arg_iterator >= argc) {
        fprintf(stderr, "Usage: %s [-E] [--color=always] PATTERN [FILE]\n",
            argv[0]);
        return INVALID_ARGUMENT;
    }

    // get file nad pattern arguments
    pattern = argv[arg_iterator++];
    if (arg_iterator < argc) {
        filename = argv[arg_iterator];
    }

    // try to open file
    FILE* file = stdin; // read from stdin as default
    if (filename) {
        file = fopen(filename, "r");
        if (!file) {
            fprintf(stderr, "Cannot open file: %s\n", filename);
            return FILE_READ_ERROR;
        }
    }

    bool found = false;
    char* line;

    while ((line = read_line(file)) != NULL) {
        int line_matched = 0;

        if (use_regular) {
            line_matched = str_regmatch(line, pattern);
        } else {
            line_matched = str_match(line, pattern);
        }

        if (line_matched) {
            if (use_color && !use_regular) {
                colorprint(line, pattern);
            } else {
                fputs(line, stdout);
            }
            found = true;
        }
        free(line);
    }

    if (file != stdin)
        fclose(file);
    return found ? FOUND : NOT_FOUND;
}

int c_strlen(const char* str)
{
    /*
        get string length
    */

    int len = 0;
    while (*str++ != '\0') { // count char by char
        len++;
    }
    return len;
}

bool c_strcmp(const char* a, const char* b)
{
    /*
        check if two strings are identical
    */

    while (*a != '\0' && *b != '\0') {
        if (*a != *b) {
            return false; // missmatch
        }
        a++;
        b++;
    }
    if (*a == '\0' && *b == '\0') { // if both strings ending at same position
        return true; // OK
    } else {
        return false; // missmatch
    }
}

bool str_match(const char* text, const char* pattern)
{
    /*
        check if pattern is a substring of text
    */

    int text_len = c_strlen(text);
    int pattern_len = c_strlen(pattern);
    if (pattern_len == 0)
        return true; // empty str allways matches

    for (int i = 0; i <= text_len - pattern_len; i++) {
        bool match = true;
        for (int j = 0; j < pattern_len; j++) {
            if (text[i + j] != pattern[j]) {
                match = false;
                break;
            }
        }
        if (match)
            return true; // terminate right after found
    }
    return false;
}

bool str_regmatch(const char* text, const char* pattern)
{
    /*
        check if pattern given by simple regex is in text
    */

    int pattern_len = c_strlen(pattern);

    // look for modifiers
    for (int i = 0; i < pattern_len; i++) {
        char modifier = pattern[i];

        if (modifier == '*' || modifier == '+' || modifier == '?') {
            if (i == 0)
                return false; // at start has no sense
            char repeated_char = pattern[i - 1];
            int prefix_len = i - 1;
            int suffix_len = pattern_len - i - 1;

            // before modifier
            char* prefix = malloc(prefix_len + 1);
            for (int j = 0; j < prefix_len; j++)
                prefix[j] = pattern[j];
            prefix[prefix_len] = '\0';

            // after modifier
            char* suffix = malloc(suffix_len + 1);
            for (int j = 0; j < suffix_len; j++)
                suffix[j] = pattern[i + 1 + j];
            suffix[suffix_len] = '\0';

            int text_len = c_strlen(text);

            // match at every position
            for (int start = 0; start <= text_len; start++) {
                int pos = start;
                bool matched = true;

                // match prefix
                for (int j = 0; j < prefix_len; j++) {
                    if (text[pos] == '\0' || text[pos] != prefix[j]) {
                        matched = false;
                        break;
                    }
                    pos++;
                }

                if (!matched)
                    continue;

                int repeat_count = 0;
                while (text[pos] == repeated_char) {
                    pos++;
                    repeat_count++;
                }

                if (!((modifier == '*' && repeat_count >= 0)
                        || (modifier == '+' && repeat_count >= 1)
                        || (modifier == '?' && repeat_count <= 1)))
                    continue;

                // match suffix
                for (int j = 0; suffix[j] != '\0'; j++) {
                    if (text[pos] == '\0' || text[pos] != suffix[j]) {
                        matched = false;
                        break;
                    }
                    pos++;
                }

                if (matched) {
                    free(prefix);
                    free(suffix);
                    return true;
                }
            }

            free(prefix);
            free(suffix);
            return false;
        }
    }
    return str_match(text, pattern);
}

void colorprint(const char* text, const char* pattern)
{
    /*
        print visualize match by adding color escape code
    */

    int tlen = c_strlen(text);
    int plen = c_strlen(pattern);

    for (int i = 0; i < tlen;) {
        int match = 1;
        for (int j = 0; j < plen; j++) {
            if (i + j >= tlen || text[i + j] != pattern[j]) {
                match = 0;
                break;
            }
        }

        if (match) {
            fputs(COLOR_START, stdout);
            for (int j = 0; j < plen; j++)
                putchar(text[i + j]);
            fputs(COLOR_END, stdout);
            i += plen;

        } else {
            putchar(text[i++]);
        }
    }
}

char* read_line(FILE* file)
{
    /*
        read one line from file
    */

    size_t size = 64; // default chunk to be allocated
    size_t len = 0;
    char* buffer = malloc(size);
    if (!buffer)
        return NULL;

    int current;
    while ((current = fgetc(file)) != EOF) { // returns int, not char!
        if (len + 1 >= size) {
            size *= 2;
            char* new_buffer = realloc(buffer, size);
            if (!new_buffer) {
                free(buffer);
                return NULL;
            }
            buffer = new_buffer;
        }
        buffer[len++] = (char)current;
        if (current == '\n')
            break;
    }

    if (len == 0 && current == EOF) { // empty file
        free(buffer);
        return NULL;
    }

    buffer[len] = '\0';
    return buffer;
}
