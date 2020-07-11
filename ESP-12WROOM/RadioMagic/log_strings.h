/**
 * \file log_strings.h
 * \bried Definition of the server log strings and the predefined
 * strings to build the http answer pages.
 */

#ifndef _LOG_STRINGS
#define _LOG_STRINGS

// Server error codes
#define ERR_ARGS "Error code 001\n\n"     ///< Wrong number of arguments
#define ERR_PARM "Error code 002\n\n"     ///< Wrong parameter name
#define ERR_METHOD "Error code 003\n\n"   ///< Wrong client method (should be GET)

// Server messages
#define APP_VERSION "RadioMagic AP+Server V.1.0"
#define ERROR404 "Error 404 - RadioMagic\ninvalid request\n\n"
#define OPERATION_COMPLETE "Ok"

#endif
