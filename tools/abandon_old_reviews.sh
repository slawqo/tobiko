#!/usr/bin/env bash
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# WARNING!
# Please do not run this script without talking to the Tobiko Core team. Auto
# abandoning people's changes is a good thing, but must be done with care.
#
# before you run this modify your .ssh/config to create a
# review.opendev.org entry:
#
#   Host review.opendev.org
#   User <yourgerritusername>
#   Port 29418
#

# Note: due to gerrit bug somewhere, this double posts messages. :(

# first purge all the reviews that are more than 4w old and blocked by a core -2

DRY_RUN=0
PROJECTS="(x/tobiko OR x/devstack-plugin-tobiko)"

function print_help {
    echo "Script to abandon patches without activity for more than 4 weeks."
    echo "Usage:"
    echo "      ./abandon_old_reviews.sh [--dry-run] [--help]"
    echo " --dry-run                    In dry-run mode it will only print what patches would be abandoned "
    echo "                              but will not take any real actions in gerrit"
    echo " --help                       Print help message"
}

while [ $# -gt 0 ]; do
    key="${1}"

    case $key in
        --dry-run)
            echo "Enabling dry run mode"
            DRY_RUN=1
            shift # past argument
        ;;
        --help)
            print_help
            exit 2
    esac
done

set -o errexit
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function abandon_review {
    local gitid=$1
    shift
    local msg=$@
    # echo ssh review.opendev.org gerrit review $gitid --abandon --message \"$msg\"
    if [ $DRY_RUN -eq 1 ]; then
        echo "Would abandon $gitid"
    else
        echo "Abandoning $gitid"
        ssh review.opendev.org gerrit review $gitid --abandon --message \"$msg\"
    fi
}

blocked_reviews=$(ssh review.opendev.org "gerrit query --current-patch-set --format json $PROJECTS status:open age:4w label:Code-Review<=-2" | jq .currentPatchSet.revision | grep -v null | sed 's/"//g')

blocked_msg=$(cat <<EOF

This review is > 4 weeks without comment and currently blocked by a
core reviewer with a -2. We are abandoning this for now.

Feel free to reactivate the review by pressing the restore button and
contacting the reviewer with the -2 on this review to ensure you
address their concerns.

EOF
)

for review in $blocked_reviews; do
    # echo ssh review.opendev.org gerrit review $review --abandon --message \"$msg\"
    echo "Blocked review $review"
    abandon_review $review $blocked_msg
done

# then purge all the reviews that are > 4w with no changes and Jenkins has -1ed

failing_reviews=$(ssh review.opendev.org "gerrit query  --current-patch-set --format json $PROJECTS status:open age:4w NOT label:Verified>=1,Zuul" | jq .currentPatchSet.revision | grep -v null | sed 's/"//g')

failing_msg=$(cat <<EOF

This review is > 4 weeks without comment, and failed Jenkins the last
time it was checked. We are abandoning this for now.

Feel free to reactivate the review by pressing the restore button and
leaving a 'recheck' comment to get fresh test results.

EOF
)

for review in $failing_reviews; do
    echo "Failing review $review"
    abandon_review $review $failing_msg
done
