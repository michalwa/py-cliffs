# py-clifford
This is an implementation of [Clifford](https://github.com/michalwa/Clifford)
(originally written in Java) for Python.

**Clifford** is a command parsing utility useful for creating internal
command line interfaces for your applications. Its syntax specification method
allows command definitions and usage help to be united with a single expression.

## Syntax
**Clifford** uses a rather intuitive syntax to specify the syntax of commands:
- `literals` specify **required** terms that the command call must contain
  in order to match the specification,
- `<parameters>` accept a single token in the command call and store its value
  for processing by the command handler,
- `(variant|groups|...)` encapsulate sequences of elements and accept only one of
  those sequences (index of the present sequence is stored for processing by the handler)
- `[optional sequences]` may or may not be present in the command call
  (boolean indicating presence is stored for processing by the handler).

## Example
To demonstrate the concept of how **Clifford** works, consider this simple command syntax
specification:

    set [loud] alarm at <hour> [(am|pm)] [every <days>] [saying <message>]

Such defined syntax accepts the following command calls:

    set alarm at 9 am
    set alarm at 9
    set alarm at 11:05 pm
    set loud alarm at 7:30 am every 'mon, tue, fri'
    set loud alarm at 2 saying "It's me!"
    set alarm at 2 am every monday saying 'Hello, world!'

But will not accept the following:

    set alarm
    set loud alarm at
    set alarm at 2
    ...

For more details on how to process the matched call check out the [example](example.py).
