#!/usr/bin/env Rscript
library('tools')
library('optparse')
library('data.table')

if (!exists('opt')) ## if opt already exists allow over-ride of command line arg processing for debugging purposes
{
  option_list = list(
      make_option(c("-p", "--pairs"), type = "character", help = "rds file containing the pairs table. The pairs table is expected to be of type data.table."),
      make_option(c("-o", "--output"), type = "character", help = "Output path for the TAB-delimited file.")
  )
  parseobj = OptionParser(option_list=option_list)
  opt = parse_args(parseobj)
}

if (is.null(opt$pairs) | is.null(opt$output))
    stop(print_help(parseobj))

if (!file.exists(opt$pairs))
    stop(sprintf('The input file "%s" does not seem to exist.', opt$pairs))

extension_of_input_file = file_ext(opt$pairs)
if(extension_of_input_file != 'rds')
    stop(sprintf('The input file must have suffix ".rds", but the file you provided ("%s") has the extension: ".%s".', opt$pairs, extension_of_input_file))

print(sprintf("Reading pairs table from %s", opt$pairs))
pairs = readRDS(opt$pairs)
if (!is.data.table(pairs))
    stop('The pairs rds file must contain a table of class "data.table". The pairs table that was provided is not of class data.table.')

print(paste0('Writing the pairs table as a TAB-delimited file: ', opt$output))
fwrite(pairs, opt$output, sep='\t')
