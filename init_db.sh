#!/bin/bash
su -l postgres -c "/etc/init.d/postgresql start && psql --command \"CREATE USER nexus WITH SUPERUSER PASSWORD 'nexus123';\""
