import commentjson, sys
import copy
import json as oldjson
import re
from functools import partial as bind
from typing import *
import os, inspect, csv

prevprint = print

def fg(color=None):
    """returns ascii escape for foreground colors

    Args:
        color (str, optional): the number of the collor to get. Defaults to None - if none return the remove color sequence instead.

    Returns (str): ascii escape for foreground colors
    """
    return "\33[38;5;" + str(color) + "m" if color else "\u001b[0m"


def bg(color=None):
    """returns ascii escape for background colors

    Args:
        color (str, optional): the number of the collor to get. Defaults to None - if none return the remove color sequence instead.

    Returns (str): ascii escape for background colors
    """
    return "\33[48;5;" + str(color) + "m" if color else "\u001b[0m"


def getcolor(color):
    """will make better later

    Args:
        color (string): one of the set colors

    Raises (ValueError): if color is not a valid color

    Returns (str): an ascii escape sequence of the color
    """
    # if plainprint:
    #     return ""
    match color.lower():
        case "end":
            return "\x1b[0m"
        case "nc":
            return "\x1b[0m"
        case "red":
            return fg(1) or "\033[0m"
        case "purple":
            return fg(92)
        case "blue":
            return fg(19)
        case "green":
            return fg(28)
        case "magenta":
            return fg(90)
        case "bright blue":
            return fg(27)
        case "yellow":
            return fg(3)
        case "bold":
            return "\033[1m"
        case "underline":
            return "\033[4m"
        case "white":
            return fg(15)
        case "cyan":
            return fg(45) or "\033[96m"
        case "orange":
            return fg(208)
        case "pink":
            return fg(213)
        case _:
            raise ValueError(f"{color} is not a valid color")



class print:
    showdebugs = True
    defaultiscolor = True

    @staticmethod
    def plain(
        *a,
        sep: str | None = " ",
        end: str | None = "\n",
        file=None,
        flush=False,
    ):
        prevprint(
            *map(str, a), getcolor("END"), sep=sep, end=end, file=file, flush=flush
        )

    @staticmethod
    def color(
        *a,
        sep: str | None = " ",
        end: str | None = "\n",
        file=None,
        flush=False,
    ):
        prevprint(
            *map(bind(formatitem, nocolor=False), a),
            getcolor("END"),
            sep=sep,
            end=end,
        )

    @staticmethod
    def __init__(
        *a,
        sep: str | None = " ",
        end: str | None = "\n",
        file=None,
        flush=False,
    ):

        if print.defaultiscolor:
            prevprint(
                *map(bind(formatitem, nocolor=False), a),
                getcolor("END"),
                sep=sep,
                end=end,
            )
        else:
            prevprint(*a, sep=sep, end=end)

    @classmethod
    def debug(
        cls,
        *a,
        sep: str | None = " ",
        end: str | None = "\n",
        file=None,
        flush=False,
    ):
        if not cls.showdebugs:
            return

        prevprint(
            f"{getcolor("BLUE")}{getcolor("BOLD")}[DEBUG]{getcolor("END")}",
            *map(bind(formatitem, nocolor=False), a),
            getcolor("END"),
            sep=sep,
            end=end,
            file=file,
            flush=flush,
        )
    @classmethod
    def info(
        cls,
        *a,
        sep: str | None = " ",
        end: str | None = "\n",
        file=None,
        flush=False,
    ):
        if not cls.showdebugs:
            return

        prevprint(
            f"{getcolor("BLUE")}{getcolor("BOLD")}[DEBUG]{getcolor("END")}",
            *map(bind(formatitem, nocolor=False), a),
            getcolor("END"),
            sep=sep,
            end=end,
            file=file,
            flush=flush,
        )

    @staticmethod
    def warn(
        *a,
        sep: str | None = " ",
        end: str | None = "\n",
        file=None,
        flush=False,
    ):

        prevprint(
            f"{getcolor("YELLOW")}{getcolor("BOLD")}[WARNING]{getcolor("END")}",
            *map(bind(formatitem, nocolor=False), a),
            getcolor("END"),
            sep=sep,
            end=end,
            file=file,
            flush=flush,
        )

    @staticmethod
    def error(
        *a,
        sep: str | None = " ",
        end: str | None = "\n",
        file=None,
        flush=False,
    ):

        prevprint(
            f"{getcolor("RED")}{getcolor("BOLD")}[ERROR]{getcolor("END")}",
            *map(bind(formatitem, nocolor=False), a),
            getcolor("END"),
            sep=sep,
            end=end,
            file=file,
            flush=flush,
        )

    @staticmethod
    def success(
        *a,
        sep: str | None = " ",
        end: str | None = "\n",
        file=None,
        flush=False,
    ):
        prevprint(
            f"{getcolor("GREEN")}{getcolor("BOLD")}[success]{getcolor("END")}",
            *map(bind(formatitem, nocolor=False), a),
            getcolor("END"),
            sep=sep,
            end=end,
            file=file,
            flush=flush,
        )

class f:
  @staticmethod
  def read(
    file,
    default="",
    asbinary=False,
    buffering: int = -1,
    encoding: str | None = None,
    errors: str | None = None,
    newline: str | None = None,
    closefd: bool = True,
    opener=None,
  ):
    if os.path.isfile(file):
      with open(
        file,
        "r" + ("b" if asbinary else ""),
        buffering=buffering,
        encoding=encoding,
        errors=errors,
        newline=newline,
        closefd=closefd,
        opener=opener,
      ) as f:
        text = f.read()
      if text:
        return text
      return default
    else:
      with open(
        file,
        "w" + ("b" if asbinary else ""),
        buffering=buffering,
        encoding=encoding,
        errors=errors,
        newline=newline,
        closefd=closefd,
        opener=opener,
      ) as f:
        f.write(default)
      return default

  @staticmethod
  def writeCsv(file, rows):
    with open(file, "w", encoding="utf-8", newline="") as f:
      w = csv.writer(f)
      w.writerows(rows)
    return rows

  @staticmethod
  def write(
    file,
    text,
    asbinary=False,
    buffering: int = -1,
    encoding: str | None = None,
    errors: str | None = None,
    newline: str | None = None,
    closefd: bool = True,
    opener=None,
  ):
    with open(
      file,
      "w" + ("b" if asbinary else ""),
      buffering=buffering,
      encoding=encoding,
      errors=errors,
      newline=newline,
      closefd=closefd,
      opener=opener,
    ) as f:
      f.write(text)
    return text

  @staticmethod
  def append(
    file,
    text,
    asbinary=False,
    buffering: int = -1,
    encoding: str | None = None,
    errors: str | None = None,
    newline: str | None = None,
    closefd: bool = True,
    opener=None,
  ):
    with open(
      file,
      "a",
      buffering=buffering,
      encoding=encoding,
      errors=errors,
      newline=newline,
      closefd=closefd,
      opener=opener,
    ) as f:
      f.write(text)
    return text

  @staticmethod
  def writeline(
    file,
    text,
    buffering: int = -1,
    encoding: str | None = None,
    errors: str | None = None,
    newline: str | None = None,
    closefd: bool = True,
    opener=None,
  ):
    with open(
      file,
      "a",
      buffering=buffering,
      encoding=encoding,
      errors=errors,
      newline=newline,
      closefd=closefd,
      opener=opener,
    ) as f:
      f.write("\n" + text)
    return text


def dictmerge(dict1, dict2, reversePriority=False):
  """
  Merge two dictionaries into one, with the second dictionary's values taking priority over the first dictionary's values.
  If a key in both dictionaries is a list, append all items from the second dictionary's list to the first dictionary's list.
  If a key in both dictionaries is a sub-dictionary, recursively merge the sub-dictionaries.
  If reversePriority is True, prioritize the first dictionary's values over the second dictionary's values.

  Parameters:
    dict1 (dict): The base dictionary.
    dict2 (dict): The secondary dictionary whose values take priority.
    reversePriority (bool): Whether to prioritize the first dictionary's values. Default: False.

  Returns (dict:): The merged dictionary.
  """
  for key, value in dict2.items():
    if isinstance(value, list) and key in dict1:
      for listitem in value:
        if listitem not in dict1[key]:
          dict1[key].append(listitem)
    elif isinstance(value, dict) and key in dict1:
      dictmerge(dict1[key], value, reversePriority=reversePriority)
    else:
      if not reversePriority or key not in dict1:
        dict1[key] = value
  return dict1


def formatitem(item, tab=-2, isarrafterdict=False, nocolor=False):
    """formats data into a string

    Args:
        item (any): the item to format
        tab (): - DONT SET MANUALY
        isarrafterdict (): - DONT SET MANUALY

    Returns (str): the formatted string
    """

    class _class:
        pass

    def _func():
        pass

    def stringify(obj):
        def replace_unstringables(value):

            if type(value) in [type(_func), type(_class)]:
                return f"<{value.__name__}>"
            return value

        def convert(obj):
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert(v) for v in obj]
            return replace_unstringables(obj)

        return oldjson.dumps(convert(obj))

    wrapat = 80
    tab += 2
    TYPENAME = ""
    c = (lambda x: "") if nocolor else getcolor
    try:
        # print.plain(item, tab)
        if item == True and type(item) == type(True):
            return "True"
        if item == False and type(item) == type(False):
            return "False"
        if type(item) in [type(_class), type(_func)]:
            return f"{c("RED")}<{"class" if type(item)==type(_class) else "function"} {c("BOLD")}{c("BLUE")}{item.__name__}{c("END")}{c("RED")}>{c("END")}"
        if isinstance(item, str):
            return (
                c("purple")
                + '"'
                + str(item).replace("\\", "\\\\").replace('"', '\\"')
                + '"'
                + c("END")
            )
        if isinstance(item, int) or isinstance(item, float):
            item = str(item)
            reg = [r"(?<=\d)(\d{3}(?=(?:\d{3})*(?:$|\.)))", r",\g<0>"]
            if "." in item:
                return (
                    c("GREEN")
                    + re.sub(reg[0], reg[1], item.split(".")[0])
                    + "."
                    + item.split(".")[1]
                    + c("END")
                )
            return c("GREEN") + re.sub(reg[0], reg[1], item) + c("END")
            # Σ╘╬╧╨╤╥╙╘╒╓╖╕╔╛╙╜╝╚╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬╭╮╯╰╱╲╳╴╵╶╷╸╹╺╻╼╽╾╿

        def name(item):
            try:
                return f'{c("pink")}╟{item.__name__}╣{c("END")}'
                # return f'{c("pink")}╟{item.__name__}╿{item.__class__.__name__}╣{c("END")}'
            except:
                return f'{c("pink")}╟{item.__class__.__name__}╣{c("END")}'

        # TYPENAME=name(item)

        if not (isinstance(item, dict) or isinstance(item, list)):
            if isinstance(item, tuple):
                TYPENAME = name(item)
            else:
                try:
                    temp = [*item]
                    TYPENAME = name(item)
                    item = temp
                except:
                    try:
                        temp = {**item}
                        TYPENAME = name(item)
                        item = temp
                    except:
                        pass

        if isinstance(item, dict):
            if not len(item):
                return "{}"
            if len(stringify(item)) + tab < wrapat:
                return (
                    TYPENAME
                    + c("orange")
                    # + "\n"
                    + (" " * tab if not isarrafterdict else "")
                    + "{ "
                    + c("END")
                    + (
                        f"{c("orange")},{c("END")} ".join(
                            f"{c("purple")+(f'"{k}"' if isinstance(k, str) else formatitem(k, tab)
                                            )+c("END")}{c("orange")}:{c("END")} {formatitem(v, tab, True)}"
                            for k, v in item.items()
                        )
                    )
                    + c("orange")
                    + " }"
                    + c("END")
                )
            else:
                return (
                    TYPENAME
                    + c("orange")
                    # + "\n"
                    + (" " * tab if not isarrafterdict else "")
                    + "{"
                    + c("END")
                    + "\n  "
                    + (
                        f"{c("orange")},{c("END")}\n  ".join(
                            f"{c("purple")+(" "*tab)+(f'"{k}"' if isinstance(k, str) else formatitem(
                                k, tab))+c("END")}{c("orange")}:{c("END")} {formatitem(v, tab, True)}"
                            for k, v in item.items()
                        )
                    )
                    + "\n"
                    + c("orange")
                    + " " * tab
                    + "}"
                    + c("END")
                )
        if isinstance(item, list):
            if len(stringify(item)) + tab < wrapat:
                return (
                    TYPENAME
                    + c("orange")
                    + ("" if isarrafterdict else " " * tab)
                    + "[ "
                    + c("END")
                    + (
                        f"{c("orange")},{c("END")} ".join(
                            map(
                                lambda newitem: formatitem(newitem, tab),
                                item,
                            )
                        )
                    )
                    + c("orange")
                    + " ]"
                    + c("END")
                )
            else:
                return (
                    TYPENAME
                    + c("orange")
                    + ("" if isarrafterdict else " " * tab)
                    + "[\n"
                    + c("END")
                    + (
                        f"{c("orange")},{c("END")}\n".join(
                            map(
                                lambda newitem: (
                                    "  " + " " * tab
                                    if isinstance(newitem, str)
                                    or isinstance(newitem, int)
                                    or isinstance(newitem, float)
                                    else ""
                                )
                                + formatitem(newitem, tab),
                                item,
                            )
                        )
                    )
                    + c("orange")
                    + "\n"
                    + " " * tab
                    + "]"
                    + c("END")
                )

        return " " * tab + name(item) + '"' + str(item).replace('"', '\\"') + '"'
    except Exception as e:
        print.plain(e)
        return " " * tab + f"{c("red")}{repr(item)}{c("end")}"




import inspect

caller_file = None

for frame in inspect.stack():
  path = frame.filename

  # Skip non-python files
  if not path.endswith(".py"):
    continue

  # Skip virtualenv + site-packages
  if ".venv" in path:
    continue
  if "site-packages" in path:
    continue
  if "debugpy" in path:
    continue

  caller_file = path
  break # first valid real python file

# Fallback safety
if caller_file is None:
  caller_file = __file__

MAIN_FILE_DIR = os.path.dirname(os.path.abspath(caller_file))
LOG_FILE_NAME = os.path.splitext(os.path.basename(caller_file))[0] + ".ans"

# print(hasattr(sys.modules["__main__"], "__file__"), 'hasattr(sys.modules["__main__"], "__file__")')
# if hasattr(sys.modules["__main__"], "__file__"):
#   p = sys.modules["__main__"].__file__
#   assert isinstance(p, str)
#   caller_file = Path(p).resolve()
#   main_dir = caller_file.parent
# else:
#   # fallback (interactive shell, etc.)
#   main_dir = Path.cwd()

# os.chdir(main_dir)


def fg(color=None):
  """returns ascii escape for foreground colors

  Args:
    color (str, optional): the number of the collor to get. Defaults to None - if none return the remove color sequence instead.

  Returns (str): ascii escape for foreground colors
  """
  return "\33[38;5;" + str(color) + "m" if color else "\u001b[0m"


def bg(color=None):
  """returns ascii escape for background colors

  Args:
    color (str, optional): the number of the collor to get. Defaults to None - if none return the remove color sequence instead.

  Returns (str): ascii escape for background colors
  """
  return "\33[48;5;" + str(color) + "m" if color else "\u001b[0m"


from functools import partial as bind
from typing import *
import os
import inspect
import csv


class CustomPrint(Protocol):
  """Defines the 'shape' of our print function so Mypy doesn't complain."""

  showdebug: bool
  showinfo: bool
  defaultiscolor: bool

  def __call__(
    self,
    *a: Any,
    sep: str = " ",
    end: str = "\n",
    file: Any = None,
    flush: bool = False,
  ) -> None: ...
  def plain(
    self,
    *a: Any,
    sep: str = " ",
    end: str = "\n",
    file: Any = None,
    flush: bool = False,
  ) -> None: ...
  def debug(
    self,
    *a: Any,
    sep: str = " ",
    end: str = "\n",
    file: Any = None,
    flush: bool = False,
  ) -> None: ...
  def info(
    self,
    *a: Any,
    sep: str = " ",
    end: str = "\n",
    file: Any = None,
    flush: bool = False,
  ) -> None: ...
  def warn(
    self,
    *a: Any,
    sep: str = " ",
    end: str = "\n",
    file: Any = None,
    flush: bool = False,
  ) -> None: ...
  def error(
    self,
    *a: Any,
    sep: str = " ",
    end: str = "\n",
    file: Any = None,
    flush: bool = False,
  ) -> None: ...
  def success(
    self,
    *a: Any,
    sep: str = " ",
    end: str = "\n",
    file: Any = None,
    flush: bool = False,
  ) -> None: ...


# --- Logic Implementation ---

def format_and_log(
  prefix_type: str,
  *a: Any,
  sep=" ",
  end="\n",
  format_items=True,
  file=None,
  flush=False,
):

  if format_items:
    formatted_args = map(bind(formatitem, nocolor=False), a)
    prevprint(
      prefix_type,
      *formatted_args,
      getcolor("end"),
      sep=sep,
      end=end,
      file=file,
      flush=flush,
    )
  else:
    prevprint(prefix_type, *a, sep=sep, end=end, file=file, flush=flush)


def formatitem(item: Any, tab=-2, isarrafterdict=False, nocolor=False):
  """formats data into a string

  Args:
    item (any): the item to format
    tab (): - DONT SET MANUALLY
    isarrafterdict (): - DONT SET MANUALLY

  Returns (str): the formatted string
  """

  class _class:
    pass

  def _func():
    pass

  def stringify(obj):
    def replace_unstringables(value):

      if type(value) in [type(_func), type(_class)]:
        return f"<{value.__name__}>"
      return value

    def convert(obj: Any):
      if isinstance(obj, dict):
        return {k: convert(v) for k, v in obj.items()}
      if isinstance(obj, list):
        return [convert(v) for v in obj]
      return replace_unstringables(obj)

    return oldjson.dumps(convert(obj))

  wrapat = 80
  tab += 2
  TYPENAME = ""
  c = (lambda x: "") if nocolor else getcolor
  try:
    # print.plain(item, tab)
    if item == True and type(item) == type(True):
      return "True"
    if item == False and type(item) == type(False):
      return "False"
    if type(item) in [type(_class), type(_func)]:
      return f'{c("RED")}<{"class" if type(item)==type(_class) else "function"} {c("BOLD")}{c("BLUE")}{item.__name__}{c("END")}{c("RED")}>{c("END")}' # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
    if isinstance(item, str):
      return (
        c("purple")
        + '"'
        + str(item)
        # + str(item).replace("\\", "\\\\").replace('"', '\\"')
        + '"'
        + c("END")
      )
    if isinstance(item, int) or isinstance(item, float):
      item = str(item)
      reg = [r"(?<=\d)(\d{3}(?=(?:\d{3})*(?:$|\.)))", r",\g<0>"]
      if "." in item:
        return (
          c("GREEN")
          + re.sub(reg[0], reg[1], item.split(".")[0])
          + "."
          + item.split(".")[1]
          + c("END")
        )
      return c("GREEN") + re.sub(reg[0], reg[1], item) + c("END")
      # Σ╘╬╧╨╤╥╙╘╒╓╖╕╔╛╙╜╝╚╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬╭╮╯╰╱╲╳╴╵╶╷╸╹╺╻╼╽╾╿

    def name(item):
      try:
        return f'{c("pink")}╟{item.__name__}╣{c("END")}'
        # return f'{c("pink")}╟{item.__name__}╿{item.__class__.__name__}╣{c("END")}'
      except:
        return f'{c("pink")}╟{item.__class__.__name__}╣{c("END")}'

    # TYPENAME=name(item)

    if not (isinstance(item, dict) or isinstance(item, list)):
      if isinstance(item, tuple):
        TYPENAME = name(item) # pyright: ignore[reportConstantRedefinition]
      else:
        try:
          temp = [*item]
          TYPENAME = name( # pyright: ignore[reportConstantRedefinition]
            item # pyright: ignore[reportAny]
          )
          item = temp
        except:
          try:
            temp = {**item}
            TYPENAME = name( # pyright: ignore[reportConstantRedefinition]
              item
            )
            item = temp
          except:
            pass

    if isinstance(item, dict):
      strlen = 9999999
      try:
        strlen = len(stringify(item))
      except Exception as e:
        pass
      if not len(item):
        return f'{c("orange")}{"{}"}{c("END")}'
      if strlen + tab < wrapat:
        if strlen + tab < wrapat:
          return (
            TYPENAME
            + c("orange")
            + (" " * tab if not isarrafterdict else "")
            + "{ "
            + c("END")
            + (
              f'{c("orange")},{c("END")} '.join(
                (
                  c("purple")
                  + (
                    f'"{k}"'
                    if isinstance(k, str)
                    else formatitem(k, 0)
                  )
                  + c("END")
                  + c("orange")
                  + ":"
                  + c("END")
                  + " "
                  + formatitem(v, 0, True)
                )
                for k, v in item.items()
              )
            )
            + c("orange")
            + " }"
            + c("END")
          )

      else:
        return (
          TYPENAME
          + c("orange")
          + (" " * tab if not isarrafterdict else "")
          + "{"
          + c("END")
          + "\n  "
          + (
            (c("orange") + "," + c("END") + "\n  ").join(
              (
                c("purple")
                + (" " * tab)
                + (
                  f'"{k}"'
                  if isinstance(k, str)
                  else formatitem(k, tab)
                )
                + c("END")
                + c("orange")
                + ":"
                + c("END")
                + " "
                + formatitem(v, tab, True)
              )
              for k, v in item.items()
            )
          )
          + "\n"
          + c("orange")
          + (" " * tab)
          + "}"
          + c("END")
        )

    if isinstance(item, list):
      strlen = 9999999
      try:
        strlen = len(stringify(item))
      except Exception as e:
        pass
      if not len(item):
        return f'{c("orange")}[]{c("END")}'
      if strlen + tab < wrapat:
        return (
          TYPENAME
          + c("orange")
          + ("" if isarrafterdict else " " * tab)
          + "[ "
          + c("END")
          + (
            f"{c('orange')},{c('END')} ".join(
              map(
                lambda newitem: formatitem(newitem, -2),
                item,
              )
            )
          )
          + c("orange")
          + " ]"
          + c("END")
        )
      else:
        return (
          TYPENAME
          + c("orange")
          + ("" if isarrafterdict else " " * tab)
          + "[\n"
          + c("END")
          + (
            f"{c('orange')},{c('END')}\n".join(
              map(
                lambda newitem: (
                  "  " + " " * tab
                  if isinstance(newitem, str)
                  or isinstance(newitem, int)
                  or isinstance(newitem, float)
                  else ""
                )
                + formatitem(newitem, tab),
                item,
              )
            )
          )
          + c("orange")
          + "\n"
          + " " * tab
          + "]"
          + c("END")
        )

    return " " * tab + name(item) + '"' + str(item) + '"'
    # return " " * tab + name(item) + '"' + str(item).replace('"', '\\"') + '"' #
  except Exception as e:
    print.plain(e)
    return " " * tab + f"{c('red')}{repr(item)}{c('end')}"


# print(f'changing dir to "{os.path.dirname(os.path.abspath(caller_file))}"')
# os.chdir(os.path.dirname(os.path.abspath(caller_file)))


class json:
  """
  A class for working with JSON data.

  This class provides methods for parsing and merging JSON data, as well as setting folder icons.
  """

  @staticmethod
  def parseincludes(
    parent, innerjson=None, splitpathat="/", previnnerjson=None
  ) -> dict | list:
    """
    Recursively merge included JSON data into a parent dictionary.

    This method traverses the parent dictionary and includes referenced JSON data from specified paths.
    If a path is invalid or a recursion error occurs, an error message will be printed.

    Parameters:
      parent (dict): The parent dictionary to merge into.
      innerjson : SHOULD NOT BE SET
      splitpathat (str): The path separator to use when splitting include paths. Defaults to "/".
      previnnerjson : SHOULD NOT BE SET

    Returns (dict): The merged dictionary with included JSON data.
    """

    def ref(mainjson, thisjson=None):
      thisjson = copy.deepcopy(mainjson if thisjson is None else thisjson)
      if isinstance(thisjson, dict) and "#include" in thisjson:
        if not isinstance(thisjson["#include"], list):
          print.error(
            f"JSONREF: #include should be a list not a {type(thisjson["#include"])}",
            thisjson,
          )
          # os._exit(-1)
          raise TypeError(
            f"JSONREF: #include should be a list not a {type(thisjson["#include"])}"
          )
        for include in thisjson["#include"]:
          try:
            jsonatpath = mainjson
            for pathpart in (
              include.split(splitpathat) if splitpathat else [include]
            ):
              jsonatpath = jsonatpath[pathpart]
            newref = ref(mainjson, jsonatpath)
            # if isinstance(newref, list):
            #     key = include.split(splitpathat)[-1]
            #     if key in thisjson and thisjson[key]:
            #         thisjson[key] += newref
            #     else:
            #         thisjson[key] = newref
            # elif isinstance(newref, dict):
            dictmerge(thisjson, newref, reversePriority=True)
          except (RecursionError, KeyError) as e:
            if isinstance(e, KeyError):
              print.warn(
                f"JSONREF: error accessing included path {showpath(include)} originating from path {
                  showpath(key)}"
              )
            elif isinstance(e, RecursionError):
              print.error(
                f"JSONREF: recursion error found when reading included path {
                  showpath(include)} originating from path {showpath(key)}"
              )
              raise e
        del thisjson["#include"]
      if isinstance(thisjson, list):
        for item in thisjson:
          if isinstance(item, dict) and "#include" in item:
            thisjson.remove(item)
            lastthisjson = copy.deepcopy(thisjson)
            thisjson = []
            # asdasdajkasdgasdjksadjkasdgsadkgjsajkasdgkjgassdagkjasd
            if not isinstance(item["#include"], list):
              print.error(
                f"JSONREF: #include should be a list not a {type(item["#include"])}",
                thisjson,
              )
              # os._exit(-1)
              raise TypeError(
                f"JSONREF: #include should be a list not a {type(item["#include"])}"
              )

            for include in item["#include"]:
              try:
                jsonatpath = mainjson
                for pathpart in (
                  include.split(splitpathat)
                  if splitpathat
                  else [include]
                ):
                  jsonatpath = jsonatpath[pathpart]
                newref = ref(mainjson, jsonatpath)
                if isinstance(newref, list):
                  thisjson += newref
              except (RecursionError, KeyError) as e:
                if isinstance(e, KeyError):
                  print.warn(
                    f"JSONREF: error accessing included path {showpath(include)} originating from path {
                        showpath(key)}"
                  )
                elif isinstance(e, RecursionError):
                  print.error(
                    f"JSONREF: recursion error found when reading included path {
                        showpath(include)} originating from path {showpath(key)}"
                  )
                  raise e
            thisjson += lastthisjson
            # asdasd
      return copy.deepcopy(thisjson)

    if innerjson is None:
      innerjson = parent
    if isinstance(innerjson, list):
      for item in innerjson:
        if isinstance(item, list):
          json.parseincludes(
            parent, item, splitpathat=splitpathat, previnnerjson=innerjson
          )
        if isinstance(item, dict):
          if "#include" in item:
            for key, val in previnnerjson.items(): # type: ignore
              if val == innerjson:
                previnnerjson[key] = ref(parent, innerjson) # type: ignore
                break
          json.parseincludes(
            parent, item, splitpathat=splitpathat, previnnerjson=innerjson
          )
    else:
      for key, val in innerjson.items():
        if isinstance(val, list):
          json.parseincludes(
            parent, val, splitpathat=splitpathat, previnnerjson=innerjson
          )
        if isinstance(val, dict):
          innerjson[key] = ref(parent, innerjson[key])
          json.parseincludes(
            parent,
            innerjson[key],
            splitpathat=splitpathat,
            previnnerjson=innerjson,
          )
    return parent

  @staticmethod
  def parse(json: str) -> list | dict:
    """Parse a JSON string into a Python object ignoring comments.

    This method removes any // or /* */ style comments from the input JSON string before parsing it.

    Parameters:
      json (str): The JSON string to parse.

    Returns (list | dict): The parsed JSON data.
    """
    json = re.sub(
      r"^ *//.*$\n?", "", json, flags=re.MULTILINE
    ) # remove // comments
    json = re.sub(
      r"^ */\*[\s\S]*?\*\/$", "", json, flags=re.MULTILINE
    ) # remove /**/ comments
    json = re.sub(
      r"(,\s+)\}", "}", json, flags=re.MULTILINE
    ) # remove extra trailing commas
    json = re.sub(
      r"(,\s+)\]", "]", json, flags=re.MULTILINE
    ) # remove extra trailing commas
    return commentjson.loads(json)

  @staticmethod
  def str(obj, indent=False):
    if indent:
      return oldjson.dumps(obj, indent=2)
    else:
      return oldjson.dumps(obj)
