#!/bin/bash

# ========================================================================
# The run name can differentiate multiple chef runs on same base node
# ========================================================================

if [ "X" == "X$1" ]; then
  echo "argument required, the run name"
  exit 1
fi

RUN_NAME=$1

# the archive url can be passed in as an optional second argument
if [ "X$2" == "X" ]; then
    COOKBOOKS_ARCHIVE_URL="https://github.com/nimbusproject/phantom-cookbooks/archive/master.tar.gz"
else
    COOKBOOKS_ARCHIVE_URL=$2
fi

CHEF_LOGLEVEL="debug"
COOKBOOKS_DIR="/opt/cookbooks"
COOKBOOKS_ARCHIVE_PATH="/opt/cookbooks.tar.gz"

# ========================================================================

CMDPREFIX=""
if [ `id -u` -ne 0 ]; then
  CMDPREFIX="sudo "
fi

if [ ! -d /opt ]; then 
  $CMDPREFIX mkdir /opt
  if [ $? -ne 0 ]; then
      exit 1
  fi
fi

$CMDPREFIX wget -O $COOKBOOKS_ARCHIVE_PATH $COOKBOOKS_ARCHIVE_URL
if [ $? -ne 0 ]; then
  exit 1
fi

if [ -d $COOKBOOKS_DIR ]; then
  $CMDPREFIX mv $COOKBOOKS_DIR $COOKBOOKS_DIR.`date +%s`
  if [ $? -ne 0 ]; then
      exit 1
  fi
fi

$CMDPREFIX mkdir $COOKBOOKS_DIR
if [ $? -ne 0 ]; then
  exit 1
fi

$CMDPREFIX tar xzf $COOKBOOKS_ARCHIVE_PATH -C $COOKBOOKS_DIR --strip 1
if [ $? -ne 0 ]; then
  exit 1
fi

$CMDPREFIX mkdir -p /opt/run/$RUN_NAME
if [ $? -ne 0 ]; then
  exit 1
fi

$CMDPREFIX mkdir -p /opt/tmp
if [ $? -ne 0 ]; then
  exit 1
fi

$CMDPREFIX chmod 600 bootconf.json
$CMDPREFIX cp bootconf.json /opt/run/$RUN_NAME/chefroles.json
if [ $? -ne 0 ]; then
  exit 1
fi

cat >> chefconf.rb << "EOF"
cookbook_path "/opt/cookbooks"
log_level :debug
file_store_path "/opt/tmp"
file_cache_path "/opt/tmp"
Chef::Log::Formatter.show_time = true

EOF

$CMDPREFIX mv chefconf.rb /opt/run/$RUN_NAME/chefconf.rb
if [ $? -ne 0 ]; then
  exit 1
fi

cat >> rerun-chef-$RUN_NAME.sh << "EOF"
#!/bin/bash
CHEFLEVEL="debug"
if [ "X" != "X$1" ]; then
  CHEFLEVEL=$1
fi
EOF

echo "chef-solo -l \$CHEFLEVEL -c /opt/run/$RUN_NAME/chefconf.rb -j /opt/run/$RUN_NAME/chefroles.json" >> rerun-chef-$RUN_NAME.sh
echo 'exit $?' >> rerun-chef-$RUN_NAME.sh

chmod +x rerun-chef-$RUN_NAME.sh
if [ $? -ne 0 ]; then
  exit 1
fi

$CMDPREFIX mv rerun-chef-$RUN_NAME.sh /opt/rerun-chef-$RUN_NAME.sh
if [ $? -ne 0 ]; then
  exit 1
fi

echo "Running chef-solo"
$CMDPREFIX /opt/rerun-chef-$RUN_NAME.sh  #debug
if [ $? -ne 0 ]; then
  exit 1
fi
