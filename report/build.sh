#!/bin/sh

# Produce test HTML report file into ${REPORT_DIR}

set -xeu


TESTR_DIR=${TESTR_DIR:-$(pwd)}
BUILD_DIR=${BUILD_DIR:-${TESTR_DIR}/report/build}
SUBUNIT_FILE=${SUBUNIT_FILE:-${BUILD_DIR}/last.subunit}
TESTR_RESULTS_HTML=${TESTR_RESULTS_HTML:-${BUILD_DIR}/testr_results.html}

make_testr_results_html() {
    mkdir -p "$(dirname ${SUBUNIT_FILE})"
    (cd "${TESTR_DIR}" && stestr last --subunit) > "${SUBUNIT_FILE}"
    (cd "${BUILD_DIR}" && subunit2html "${SUBUNIT_FILE}" "${TESTR_RESULTS_HTML}")
}

make_testr_results_html
