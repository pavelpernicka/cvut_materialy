#include <stdio.h>

static char *day_of_week[] = {"Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"};
static char *name_of_month[] = {
	"January",
	"February",
	"March",
	"April",
	"May",
	"June",
	"July",
	"August",
	"September",
	"October",
	"November",
	"December"};
static int days_in_month[] = {31, 29, 31, 30, 31, 30,
							  31, 31, 30, 31, 30, 31};
static int first_day_in_september = 1; // 1. 9. 2020 is Tuesday
static int first_day_in_year = 2; // 1. 1. 2020 is Wednesday
 
void prt_days_header();
void prt_days_table(int, int);
void prt_month(char *, int, int);
int get_first_day_in_month(int);
void prt_months(int, int);

int main(void)
{

	// TODO

	return 0;
}
