from util.versionstamp import versionstamp



if __name__=="__main__":
    v = versionstamp()
    for n in range(10):
        print(v.make(), v.partition(v.make()), v.validate(v.make()))

