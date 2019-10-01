#!/bin/sh

# Produce test HTML report file into ${REPORT_DIR}

set -xeu


TESTR_DIR=${TESTR_DIR:-$(pwd)}
BUILD_DIR=${BUILD_DIR:-${TESTR_DIR}}
SUBUNIT_FILE=${SUBUNIT_FILE:-${BUILD_DIR}/last.subunit}
TESTR_RESULTS_HTML=${TESTR_RESULTS_HTML:-${BUILD_DIR}/tobiko_results.html}
TESTR_RESULTS_XML=${TESTR_RESULTS_XML:-${BUILD_DIR}/tobiko_results.xml}


make_testr_results_html() {
    mkdir -p "$(dirname ${SUBUNIT_FILE})"
    (cd "${TESTR_DIR}" && stestr last --subunit) > "${SUBUNIT_FILE}"
    (cd "${BUILD_DIR}" && subunit2html "${SUBUNIT_FILE}" "${TESTR_RESULTS_HTML}")
    (cd "${BUILD_DIR}" && subunit2junitxml "${SUBUNIT_FILE}" -o "${TESTR_RESULTS_XML}")
}

make_testr_results_html
