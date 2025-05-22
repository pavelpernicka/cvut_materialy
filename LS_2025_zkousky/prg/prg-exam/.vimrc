set ruler
set showcmd
set showmode
set cindent
set nowrap
set number
set shiftwidth=3
syntax on
set nocompatible
filetype plugin indent on
colo darkblue

"remember the position in file
if has("autocmd")
   autocmd BufReadPost *
	    \ if line("'\"") > 0 && line ("'\"") <= line("$") |
	    \   exe "normal g'\"" |
	    \ endif
endif

set makeprg=make

set nomodeline
map <F5> :!make<CR>
map <F9> :!make clean<CR>

set nohlsearch

set vb t_vb=
