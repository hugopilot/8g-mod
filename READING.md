# I can't read code! 
That's fine! We can give you a guide on how to read the code.
The language we're using is [**python**](https://python.org)


Firstly, most code is commented, recognizable by a line starting with `#`. Comments describe what a code section does. For example:
```py
# This is a comment. Below is an if-statement that checks if 'msg' (message) is 'hi'
if(msg == 'hi'):
  pass
```

Reading code can look intimidating, however it's not that intimidating once you realize the following:
1. Computers and their programs are based on logic operations. It's not rocket science!
2. There is a human behind every line.
3. Python looks like bare-bones english when you remove the special characters
4. Code runs in a sequence

Let's focus on bullet point nr.4: 'Code runs in a sequence'. Code runs from up to down. Take this example:
```py
# Defines a variable called msg with the value 'Hi!'
msg = "Hi!"

# Checks if 'Hi' appears in msg
if('Hi' in msg):
  # This prints 'yey' to the console
  print("yey")
```

Code can 'jump' to other sections. Example:
```py
def check_if_hi(message):
  if('Hi' in message):
    return 'Hey!'
  return 'Hey?'
  
msg = "Hi!"

result = check_if_hi(msg)
print(result)
```
The code here actually starts at `msg = "Hi!` and jumps to `def check_if_hi(message)` once the program reaches `result = check_if_hi(msg)`. 
After execution of the `check_if_hi(message)` function the progam put the returning value in `result`. Finally the progam prints `result` with `print(result)`
  
