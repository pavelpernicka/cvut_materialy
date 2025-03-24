#include <stdio.h>
 
static int arr[5] = { 1, 2, 3, 4, 5 };
static void endless(int size)
{
    for (int i = 0; i < size; ++i)
        printf(" %d", arr[i]);
    printf("\n");
    endless(size * 10);
}
 
int main(int argc, char *argv[])
{
    endless(1);
    return 0;
}


