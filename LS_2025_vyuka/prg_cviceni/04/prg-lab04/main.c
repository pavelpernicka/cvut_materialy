#include <stdio.h>

int num = 4;

int main(int argc, char const *argv[])
{
    int arr[num];
    for(int i = 0; i < num; i++){
    	scanf("%d", &arr[i]);
    }
    
    for(int i = 0; i < num; i++){
    	printf("%d ", arr[i]);
    }
    return 0;
}
