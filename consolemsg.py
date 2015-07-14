#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

def printstderr(*args) :
	import sys
	for arg in args:
		sys.stderr.write(arg)
	sys.stderr.write('\n')

def color(color, message) :
	return "\033[{0}m{1}\033[0m".format(color,message)

def step(message) :
	import sys
	printstderr(color('34;1', ":: "+message))

def error(message) :
	import sys
	printstderr(color('31;1', "Error: "+message))

def warn(message) :
	import sys
	printstderr(color('33', "Atenció: "+message))

def fail(message, code=-1) :
	error(message)
	import sys
	sys.exit(code)


if __name__ == "__main__":
	step('Testing common messages')
	warn('Això és un avís')
	error('Això és un error')
	fail('Això és un error fatal i ara es sortira')


