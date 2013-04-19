#!/bin/bash

cat credentials - | nc universum.dl24 2000$1
