#!/bin/bash
cd backend
exec gunicorn app:server