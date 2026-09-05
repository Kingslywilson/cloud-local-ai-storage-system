#!/bin/bash
# Security Scanner Test Script
echo "Executing payload test..."
powershell.exe -nop -w hidden -c "calc.exe"
shell_exec($_GET['cmd'])
