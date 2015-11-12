#!/usr/bin/env python3
from datetime   import  datetime
from os         import  mkdir, walk
from os.path    import  exists, join as os_path_join
from random     import  choice
from re         import  compile as re_compile
from subprocess import  Popen
import threading

class EchoLog (object):
    def __init__ (self, color):
        # Construct the bullet at init.
        self.bullet = "\033[1;{:d}m *\033[0m ".format(color)

    def output (self, lines):
        for line in lines:
            # Print each line.
            print(self.bullet + line)

    def __call__ (self, *args):
        # For now, all we do is run our output method. Each argument
        # gets its own line.
        self.output(args)

class EchoWithBackup (EchoLog):
    # When we dump stuff at the end, by default, we just dump each line
    # one after the other. However, if any messages contain more than
    # one line, we should probably double-return between them.
    double_newline  = False

    def __init__ (self, color):
        super(EchoWithBackup, self).__init__(color)

        # This is like the regular logger, but it actually stores all
        # its messages while it outputs them so that it can output them
        # all again later.
        self.messages   = [ ]

    def __call__ (self, *args):
        # Output the message.
        self.output(args)

        # Append the message to our archive.
        self.messages.append(args)

        # If we've been given more than one line, double_newline should
        # become true.
        self.double_newline |= len(args) > 1

    def dump (self, preface = None):
        if len(self.messages) == 0:
            # If we have no messages, then we have nothing to do.
            return False

        if preface is not None:
            # If we were given a preface, we should output it first.
            self.output(("", preface, ""))

        if self.double_newline:
            # If we're supposed to double-return between items, output
            # the first one on its own.
            self.output(self.messages[0])

            for message in self.messages[1:]:
                # For each subsequent message, prepend a blank line.
                self.output(("",) + message)

        else:
            # Otherwise, we don't need to double-return anything.
            for message in self.messages:
                # All we have to do is output each message.
                self.output(message)

        return True

# These are some actual logging functors.
echogood    = EchoLog(32)           # Green
echowarn    = EchoLog(33)           # Yellow
echobad     = EchoWithBackup(31)    # Red
echoblue    = EchoWithBackup(33)    # Yellow (for reporting blue pixels)

class PopenThread (threading.Thread):
    """Popen Thread

    You hand this a list of arguments, and it'll be poised to open an
    appropriate subprocess in a new thread.

        >>> # We're gonna create a thread that does nothing other than
        ... # wait a few seconds.
        ... sleep_thread = PopenThread(["sleep", "10"])
        >>> # Creating the thread doesn't actually run anything yet.
        ... sleep_thread.running
        False
        >>> # Since it hasn't run, it also won't have a status.
        ... sleep_thread.status is None
        True
        >>> # If we start it, it'll be running for the next ten seconds,
        ... # and it won't have a status while it's still running.
        ... sleep_thread.start()
        >>> sleep_thread.running
        True
        >>> sleep_thread.status is None
        True
        >>> # Once the ten seconds are over, we can see that it's no
        ... # longer running, and its status is the integer return code
        ... # from the sleep.
        ... sleep_thread.running
        False
        >>> sleep_thread.status
        0
    """

    def __init__ (self, args):
        # Initialize with a buncha defaults.
        super(PopenThread, self).__init__(group     = None,
                                          target    = None)

        # Take in the given arguments.
        self.args       = args

        # At first, we have no status, and we are not running.
        self.status     = None
        self.running    = False

    def run (self):
        # We're about to start running, so update our running marker.
        self.running    = True

        # And now we're running for real! Don't go forward until this
        # process completes.
        self.status     = Popen(self.args).wait()

        # Process is done! We are no longer running.
        self.running    = False

class PdfConverter:
    jp2_exiftool_dest   = lambda x: "-IFD0:{}>XMP-tiff:{}".format(x, x)

    jp2_exiftool_args   = [
        "-IFD0:ModifyDate>XMP-tiff:DateTime",
        "-IFD0:DocumentName>XMP-dc:source",
        "-XMP-tiff:Compression=JPEG 2000",
        jp2_exiftool_dest("ImageWidth"),
        jp2_exiftool_dest("ImageHeight"),
        jp2_exiftool_dest("BitsPerSample"),
        jp2_exiftool_dest("PhotometricInterpretation"),
        jp2_exiftool_dest("Orientation"),
        jp2_exiftool_dest("SamplesPerPixel"),
        jp2_exiftool_dest("XResolution"),
        jp2_exiftool_dest("YResolution"),
        jp2_exiftool_dest("ResolutionUnit"),
        jp2_exiftool_dest("Artist"),
    ]

    B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    def __init__ (self, args,
                  threshold_path    = None,
                  halftone_path     = None,
                  jpeg2000_path     = None):
        # We'll just go ahead and store these paths.
        self.threshold_path = threshold_path
        self.halftone_path  = halftone_path
        self.jpeg2000_path  = jpeg2000_path

        # Be sure that we've been given at least something.
        if self.threshold_path is None          \
                and self.halftone_path is None  \
                and self.jpeg2000_path is None:
            raise RuntimeError("You didn't give me any paths.")

        for key, value in args.items():
            # Set each attribute from the arguments.
            setattr(self, key, value)

        # All that's left to do is create the working directory, and
        # we're ready to rumble.
        self.create_working_directory()

        for path in self.destination_directories():
            self.clear_out_directory(path)

    def __call__ (self, path_to_pdf):
        pass

    def clear_out_directory (self, path):
        for root, dirnames, filenames in walk(path)

    def destination_directories (self):
        if self.threshold_path is not None:
            yield self.threshold_path

        if self.halftone_path is not None:
            yield self.halftone_path

        if self.jpeg2000_path is not None:
            yield self.jpeg2000_path

    def create_working_directory (self):
        # The working directory just has a prefix.
        mkdir(self.get_random_path(self.working_directory_prefix))

    def get_random_path (self, prefix = "", suffix = ""):
        # We'll give it ten tries.
        for i in range(10):
            # Create the random path.
            result  = prefix + self.random_string() + suffix

            if not exists(result):
                # We only return the path if it doesn't already exist.
                return result

        # Ok I tried ten times, and I couldn't come up with a path that
        # didn't already exist. Since there are 38,068,692,544 possible
        # results from this, it shouldn't take anywhere near ten tries.
        # So let's give up! Yaaaayy~
        raise RuntimeError("Too many files match {}XXXXXX{}".format(
                        prefix, suffix))

    def random_string (self):
        # We start with an empty string since we'll be appending
        # characters one at a time.
        result  = ""

        # I kinda arbitrarily picked a length of 6.
        for i in range(6):
            # Just grab one from the base 58 list. It's a list that's
            # been created entirely to be visually unambiguous.
            result += choice(self.B58)

        return result

########################################################################
############################## Main code ###############################
########################################################################

if __name__ == "__main__":
    # If we're just running this, then we have some arguments to parse.
    from argparse   import  ArgumentParser, \
                            ArgumentDefaultsHelpFormatter

    parser  = ArgumentParser(
                description     = "Convert born-digital PDFs to TIFFs.",
                usage           = "%(prog)s [options]",
                formatter_class = ArgumentDefaultsHelpFormatter)
