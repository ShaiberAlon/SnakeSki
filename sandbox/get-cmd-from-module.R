#!/usr/bin/env Rscript
# ad-hoc script to parse the command line from a Flow module file.
# Most of the code here was adopted from the Flow source.
# An important difference is that here we surround keywords by "{" and "}" instead of  "<" and ">".
# This change is in order to allow the use of the python str.format() downstream.
# required packages: optparse, stringi, stringr

library('optparse')
library('stringr')

if (!exists('opt')) ## if opt already exists allow over-ride of command line arg processing for debugging purposes
{
  option_list = list(
      make_option(c("-m", "--module"), type = "character", help = "Path to module file or directory."),
      make_option(c("-o", "--output"), type = "character", help = "Output path for a TXT file containing the reformatted command.")
  )
  parseobj = OptionParser(option_list=option_list)
  opt = parse_args(parseobj)
}

file.dir = function(paths){
    # this function is copied from skitools
    return(gsub("(^|(.*\\/))?([^\\/]*)$", "\\2", paths))
}

if (is.null(opt$module) | is.null(opt$output))
    stop(print_help(parseobj))


path = opt$module

if (!file.exists(path))
    stop(sprintf('%s not found, check path', path))

if (file.info(path)$isdir){
    path = paste(path, 'hydrant.deploy', sep = '/')
} else {
    path = paste(file.dir(path), 'hydrant.deploy', sep = '/')
}

if (!file.exists(path))
    path = paste(file.dir(path), 'flow.deploy', sep = '/')

if (!file.exists(path))
    stop(sprintf('%s not found, check path.', path))

cmd.re = '^command\\s*[\\:\\=]\\s+'
cmd = gsub(cmd.re, '', grep(cmd.re, readLines(path), value = TRUE))

if (length(cmd)==0)
    stop('Problem parsing .deploy file, maybe it is an old version or a scatter gather task, which is not currently supported')

if (!grepl('sh', cmd))
    warning('Module command does not begin with "sh" - make sure that this is not a scatter gather command, which is not currently supported')


## need to replace $(\\w+ .* FEATURE_NAME) with just the internal and extract the FEATURE_NAME
pattern = '\\$\\{[a-z\\,]*( [^\\}]*)? (\\S+)\\s*\\}';
args = stringi::stri_match_all_regex(cmd, pattern, omit_no_match = TRUE, cg_missing = "")[[1]]

args[,3] = gsub('\\=.*', '', args[,3])

## create new string with clear "formats" we can sub into
cmd.new = cmd
for (i in 1:nrow(args))
    cmd.new = str_replace_all(cmd.new, stringr::fixed(args[,1][i]), paste(gsub('\\"', '', args[,2]), '{', args[,3], '}', sep = '')[i])

cat(sprintf('Writing the following command to the file %s:
              "%s"', opt$output, cmd.new))
f = file(opt$output)
writeLines(cmd.new, f)
close(f)
