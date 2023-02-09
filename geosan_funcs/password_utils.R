askForPassword <- function() {
  cat("Password:");
  password <- readLines("stdin",n=1, ok=FALSE);
  password
}